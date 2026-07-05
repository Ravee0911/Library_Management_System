"""
=========================================================
 LIBRARY MANAGEMENT SYSTEM - Main Application File
=========================================================
This file is the "brain" of our website. It:
1. Sets up the database (where we store books, members, etc.)
2. Defines "routes" (web pages) like /books, /members, etc.
3. Handles adding, editing, deleting, borrowing, and returning books

We use:
- Flask -> a simple tool for building websites in Python
- SQLite -> a simple file-based database (no separate server needed)
"""

from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import date

# ---------------------------------------------------------
# STEP 1: Create the Flask app
# ---------------------------------------------------------
app = Flask(__name__)
app.secret_key = "library-secret-key"  # needed for flash messages (little pop-up notes)

DATABASE = "library.db"


# ---------------------------------------------------------
# STEP 2: Helper function to connect to the database
# ---------------------------------------------------------
def get_db_connection():
    """
    Opens a connection to our SQLite database file.
    'row_factory' lets us access columns by name, like row["title"],
    instead of just row[0], row[1], etc. This makes the code easier to read.
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # keeps our data connections valid
    return conn


# ---------------------------------------------------------
# STEP 3: Create the database tables (only runs once)
# ---------------------------------------------------------
def init_db():
    """
    Creates three tables if they don't already exist:
    - books: information about each book
    - members: people who can borrow books
    - borrow_records: history of who borrowed what and when
    """
    conn = get_db_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT,
            total_copies INTEGER NOT NULL DEFAULT 1,
            available_copies INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS borrow_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            member_id INTEGER NOT NULL,
            borrow_date TEXT NOT NULL,
            return_date TEXT,
            FOREIGN KEY (book_id) REFERENCES books (id),
            FOREIGN KEY (member_id) REFERENCES members (id)
        );
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------
# STEP 4: HOME PAGE - shows a simple dashboard
# ---------------------------------------------------------
@app.route("/")
def home():
    conn = get_db_connection()
    total_books = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    total_members = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
    borrowed_now = conn.execute(
        "SELECT COUNT(*) FROM borrow_records WHERE return_date IS NULL"
    ).fetchone()[0]
    conn.close()
    return render_template(
        "index.html",
        total_books=total_books,
        total_members=total_members,
        borrowed_now=borrowed_now,
    )


# ---------------------------------------------------------
# STEP 5: BOOKS - list, add, edit, delete
# ---------------------------------------------------------
@app.route("/books")
def list_books():
    """Shows every book currently in the library."""
    conn = get_db_connection()
    books = conn.execute("SELECT * FROM books ORDER BY title").fetchall()
    conn.close()
    return render_template("books.html", books=books)


@app.route("/books/add", methods=["GET", "POST"])
def add_book():
    """
    GET  -> show the empty form
    POST -> the user submitted the form, so save the new book
    """
    if request.method == "POST":
        title = request.form["title"].strip()
        author = request.form["author"].strip()
        isbn = request.form.get("isbn", "").strip()
        copies = int(request.form.get("copies", 1))

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO books (title, author, isbn, total_copies, available_copies) "
            "VALUES (?, ?, ?, ?, ?)",
            (title, author, isbn, copies, copies),
        )
        conn.commit()
        conn.close()
        flash(f'Book "{title}" was added successfully!', "success")
        return redirect(url_for("list_books"))

    return render_template("add_book.html")


@app.route("/books/edit/<int:book_id>", methods=["GET", "POST"])
def edit_book(book_id):
    conn = get_db_connection()
    book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()

    if book is None:
        conn.close()
        flash("Book not found.", "error")
        return redirect(url_for("list_books"))

    if request.method == "POST":
        title = request.form["title"].strip()
        author = request.form["author"].strip()
        isbn = request.form.get("isbn", "").strip()
        new_total = int(request.form.get("copies", 1))

        # Adjust available copies if total copies changed
        difference = new_total - book["total_copies"]
        new_available = book["available_copies"] + difference
        if new_available < 0:
            new_available = 0

        conn.execute(
            "UPDATE books SET title=?, author=?, isbn=?, total_copies=?, available_copies=? "
            "WHERE id=?",
            (title, author, isbn, new_total, new_available, book_id),
        )
        conn.commit()
        conn.close()
        flash("Book updated successfully!", "success")
        return redirect(url_for("list_books"))

    conn.close()
    return render_template("edit_book.html", book=book)


@app.route("/books/delete/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    flash("Book deleted.", "success")
    return redirect(url_for("list_books"))


# ---------------------------------------------------------
# STEP 6: MEMBERS - list, add, delete
# ---------------------------------------------------------
@app.route("/members")
def list_members():
    conn = get_db_connection()
    members = conn.execute("SELECT * FROM members ORDER BY name").fetchall()
    conn.close()
    return render_template("members.html", members=members)


@app.route("/members/add", methods=["GET", "POST"])
def add_member():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()

        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO members (name, email) VALUES (?, ?)", (name, email)
            )
            conn.commit()
            flash(f'Member "{name}" added successfully!', "success")
        except sqlite3.IntegrityError:
            flash("That email is already registered.", "error")
        conn.close()
        return redirect(url_for("list_members"))

    return render_template("add_member.html")


@app.route("/members/delete/<int:member_id>", methods=["POST"])
def delete_member(member_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM members WHERE id = ?", (member_id,))
    conn.commit()
    conn.close()
    flash("Member deleted.", "success")
    return redirect(url_for("list_members"))


# ---------------------------------------------------------
# STEP 7: BORROWING a book
# ---------------------------------------------------------
@app.route("/borrow", methods=["GET", "POST"])
def borrow_book():
    conn = get_db_connection()

    if request.method == "POST":
        book_id = int(request.form["book_id"])
        member_id = int(request.form["member_id"])

        book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()

        if book is None or book["available_copies"] < 1:
            flash("Sorry, that book is not available right now.", "error")
        else:
            # Reduce available copies by 1
            conn.execute(
                "UPDATE books SET available_copies = available_copies - 1 WHERE id = ?",
                (book_id,),
            )
            # Record the borrow event with today's date
            conn.execute(
                "INSERT INTO borrow_records (book_id, member_id, borrow_date, return_date) "
                "VALUES (?, ?, ?, NULL)",
                (book_id, member_id, str(date.today())),
            )
            conn.commit()
            flash("Book borrowed successfully!", "success")
        conn.close()
        return redirect(url_for("borrow_book"))

    # GET request -> show the form with dropdowns
    books = conn.execute(
        "SELECT * FROM books WHERE available_copies > 0 ORDER BY title"
    ).fetchall()
    members = conn.execute("SELECT * FROM members ORDER BY name").fetchall()
    conn.close()
    return render_template("borrow.html", books=books, members=members)


# ---------------------------------------------------------
# STEP 8: RETURNING a book
# ---------------------------------------------------------
@app.route("/return/<int:record_id>", methods=["POST"])
def return_book(record_id):
    conn = get_db_connection()
    record = conn.execute(
        "SELECT * FROM borrow_records WHERE id = ?", (record_id,)
    ).fetchone()

    if record and record["return_date"] is None:
        conn.execute(
            "UPDATE borrow_records SET return_date = ? WHERE id = ?",
            (str(date.today()), record_id),
        )
        conn.execute(
            "UPDATE books SET available_copies = available_copies + 1 WHERE id = ?",
            (record["book_id"],),
        )
        conn.commit()
        flash("Book marked as returned. Thank you!", "success")

    conn.close()
    return redirect(url_for("history"))


# ---------------------------------------------------------
# STEP 9: HISTORY - see who has borrowed what
# ---------------------------------------------------------
@app.route("/history")
def history():
    conn = get_db_connection()
    records = conn.execute("""
        SELECT borrow_records.id, books.title, members.name, borrow_records.borrow_date,
               borrow_records.return_date
        FROM borrow_records
        JOIN books ON borrow_records.book_id = books.id
        JOIN members ON borrow_records.member_id = members.id
        ORDER BY borrow_records.borrow_date DESC
    """).fetchall()
    conn.close()
    return render_template("history.html", records=records)


# ---------------------------------------------------------
# STEP 10: Run the app
# ---------------------------------------------------------
if __name__ == "__main__":
    init_db()  # make sure tables exist before we start
    app.run(debug=True)
