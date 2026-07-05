# 📚 Library Management System

A simple, beginner-friendly library management system built with **Python**, **Flask**, and **SQLite**.

## What it can do

- Add, edit, and delete books
- Add and remove members
- Borrow a book (automatically reduces available copies)
- Return a book (automatically increases available copies)
- View full borrowing history
- Dashboard showing quick stats

## How it's organized

```
library_system/
│
├── app.py                # The main program (routes + database logic)
├── requirements.txt      # List of packages needed
├── library.db             # Database file (created automatically on first run)
│
├── templates/            # HTML pages
│   ├── base.html          # Shared layout (navbar, etc.)
│   ├── index.html         # Dashboard
│   ├── books.html         # List of books
│   ├── add_book.html      # Add book form
│   ├── edit_book.html     # Edit book form
│   ├── members.html       # List of members
│   ├── add_member.html    # Add member form
│   ├── borrow.html        # Borrow a book form
│   └── history.html       # Borrow/return history
│
└── static/
    └── style.css          # Small styling tweaks
```

## How to run it

1. **Install Python** (3.8 or newer) if you don't already have it.

2. **Open a terminal** in the `library_system` folder.

3. **Install Flask**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**:
   ```bash
   python app.py
   ```

5. **Open your browser** and go to:
   ```
   http://127.0.0.1:5000
   ```

That's it! The database file (`library.db`) is created automatically the first time you run the app — no extra setup needed.

## How the code works (in plain English)

- **`app.py`** is the control center. Every time you visit a page (like `/books`), Flask runs the matching function (like `list_books()`), which fetches data from the database and hands it to an HTML template to display.
- **SQLite** is used as the database — it's just a single file (`library.db`), so there's nothing extra to install or configure.
- **Templates** (the `.html` files) use a system called Jinja2, which lets us insert Python data into HTML using `{{ }}` and add logic using `{% %}` (like loops and if-statements).
- **Borrowing logic**: when someone borrows a book, we subtract 1 from `available_copies` and create a new row in `borrow_records`. Returning a book does the reverse and fills in the `return_date`.

## Ideas for extending it

- Add user login so each member manages their own account
- Add due dates and automatic late fees
- Add search/filter for books
- Export reports to CSV or PDF

Enjoy your library system! 🎉
