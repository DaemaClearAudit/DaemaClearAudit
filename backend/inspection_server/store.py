"""SQLite persistence for sessions and imported form submissions."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(os.getenv("INSPECTION_DB", Path(__file__).resolve().parents[1] / "data" / "inspection.sqlite3"))

@contextmanager
def connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS sessions (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'OPEN',
          created_at TEXT NOT NULL, closed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS submissions (
          id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id),
          table_id TEXT NOT NULL, photo_id TEXT NOT NULL, source_key TEXT NOT NULL,
          submitted_at TEXT, submitter TEXT, status TEXT NOT NULL DEFAULT 'RECEIVED',
          created_at TEXT NOT NULL, verdict TEXT, reason TEXT,
          UNIQUE(source_key)
        );
        CREATE INDEX IF NOT EXISTS submissions_session_table ON submissions(session_id, table_id);
        ''')
        columns = {r['name'] for r in db.execute('PRAGMA table_info(submissions)')}
        if 'verdict' not in columns:
            db.execute('ALTER TABLE submissions ADD COLUMN verdict TEXT')
        if 'reason' not in columns:
            db.execute('ALTER TABLE submissions ADD COLUMN reason TEXT')
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()
