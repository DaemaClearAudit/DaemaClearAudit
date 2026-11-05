"""SQLite persistence for sessions and imported form submissions."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(os.getenv("INSPECTION_DB", Path(__file__).resolve().parents[1] / "data" / "inspection.sqlite3"))

@contextmanager
def connection(*, write=False):
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
        CREATE TABLE IF NOT EXISTS sheet_sources (
          spreadsheet_id TEXT PRIMARY KEY, sheet_range TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS jobs (
          id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id),
          status TEXT NOT NULL, accepted_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          result TEXT, error TEXT
        );
        CREATE TABLE IF NOT EXISTS sync_conflicts (
          source_key TEXT NOT NULL, session_id TEXT NOT NULL REFERENCES sessions(id),
          reason TEXT NOT NULL, PRIMARY KEY(source_key,session_id)
        );
        ''')
        conflict_columns = {r['name']: r['pk'] for r in db.execute('PRAGMA table_info(sync_conflicts)')}
        if conflict_columns.get('session_id') != 2:
            db.executescript('''
                ALTER TABLE sync_conflicts RENAME TO sync_conflicts_old;
                CREATE TABLE sync_conflicts (
                    source_key TEXT NOT NULL, session_id TEXT NOT NULL REFERENCES sessions(id),
                    reason TEXT NOT NULL, PRIMARY KEY(source_key,session_id));
                INSERT INTO sync_conflicts SELECT source_key,session_id,reason FROM sync_conflicts_old;
                DROP TABLE sync_conflicts_old;
            ''')
        session_columns = {r['name'] for r in db.execute('PRAGMA table_info(sessions)')}
        for column in ('inspection_date', 'started_at', 'updated_at', 'last_synced_at', 'sheet_id', 'drive_folder_id', 'photos_verified'):
            if column not in session_columns:
                db.execute(f'ALTER TABLE sessions ADD COLUMN {column} TEXT')
        columns = {r['name'] for r in db.execute('PRAGMA table_info(submissions)')}
        if 'verdict' not in columns:
            db.execute('ALTER TABLE submissions ADD COLUMN verdict TEXT')
        if 'reason' not in columns:
            db.execute('ALTER TABLE submissions ADD COLUMN reason TEXT')
        if write:
            db.execute('BEGIN IMMEDIATE')
            # Normalize the initial draft's A1 notation to the documented A-01 format.
            db.execute("UPDATE submissions SET table_id = substr(table_id,1,1) || '-0' || substr(table_id,2,1) "
                       "WHERE length(table_id)=2 AND table_id GLOB '[A-D][1-4]'")
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()
