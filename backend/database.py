"""
SQLite initialization for JobFit.

Call init_db(db_path) at application startup to create the schema.
Default path: jobfit.db in the backend directory.
"""
import sqlite3
import os

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "jobfit.db")


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Create the SQLite database and tables if they do not exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            date              TEXT    NOT NULL,
            jobs_found        INTEGER NOT NULL DEFAULT 0,
            jobs_after_filter INTEGER NOT NULL DEFAULT 0,
            jobs_selected     INTEGER NOT NULL DEFAULT 0,
            status            TEXT    NOT NULL DEFAULT 'pending'
        );

        CREATE TABLE IF NOT EXISTS jobs (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id             INTEGER NOT NULL REFERENCES runs(id),
            title              TEXT,
            company            TEXT,
            location           TEXT,
            description        TEXT,
            url                TEXT,
            salary             TEXT,
            score              REAL,
            reasoning          TEXT,
            selected           INTEGER NOT NULL DEFAULT 0,
            cv_path            TEXT,
            cover_letter_path  TEXT
        );
    """)

    conn.commit()
    conn.close()
