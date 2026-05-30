import sqlite3
import os

# The database file will be created here
DATABASE_PATH = os.getenv("DATABASE_PATH", "support_crm.db")


def get_db():
    """
    Opens a connection to the SQLite database.
    check_same_thread=False is needed for FastAPI (multi-threaded).
    row_factory lets us access columns by name (like a dict).
    """
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # row["column_name"] instead of row[0]
    conn.execute("PRAGMA journal_mode=WAL")  # Better performance for concurrent reads
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # ---------- TICKETS TABLE ----------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id     TEXT UNIQUE NOT NULL,       -- e.g. TKT-001
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            subject       TEXT NOT NULL,
            description   TEXT NOT NULL,
            status        TEXT NOT NULL DEFAULT 'Open', -- Open | In Progress | Closed
            priority      TEXT NOT NULL DEFAULT 'Medium', -- Low | Medium | High
            created_at    TEXT NOT NULL,               -- ISO timestamp string
            updated_at    TEXT NOT NULL
        )
    """)

    # ---------- NOTES TABLE ----------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id  TEXT NOT NULL,                 -- FK to tickets.ticket_id
            note_text  TEXT NOT NULL,
            author     TEXT NOT NULL DEFAULT 'Support Agent',
            created_at TEXT NOT NULL,
            FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully.")