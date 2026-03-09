import sqlite3

from config import DB_PATH


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            title     TEXT NOT NULL,
            company   TEXT,
            location  TEXT,
            url       TEXT UNIQUE NOT NULL,
            keywords  TEXT,
            source    TEXT,
            job_type  TEXT,
            posted_at TEXT,
            found_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    # migrate existing databases that predate added columns
    existing = [row[1] for row in cursor.execute("PRAGMA table_info(jobs)")]
    if "source" not in existing:
        cursor.execute("ALTER TABLE jobs ADD COLUMN source TEXT")
    if "job_type" not in existing:
        cursor.execute("ALTER TABLE jobs ADD COLUMN job_type TEXT")

    conn.commit()
    conn.close()
    print("Database initialized.")


def save_job(conn, job, keyword, source):
    """Insert a job into the DB. Skips silently if URL already exists."""
    try:
        conn.execute(
            """
            INSERT INTO jobs (title, company, location, url, keywords, source, job_type, posted_at)
            VALUES (:title, :company, :location, :url, :keywords, :source, :job_type, :posted_at)
            """,
            {**job, "keywords": keyword, "source": source},
        )
        return True
    except sqlite3.IntegrityError:
        return False


if __name__ == "__main__":
    init_db()
