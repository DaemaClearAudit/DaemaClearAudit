import os
import sqlite3
import uuid
from datetime import datetime

# 데이터베이스 파일 경로 (backend/data.db)
DB_FILE = os.path.join(os.path.dirname(__file__), "data.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    inspection_date TEXT,
    started_at TEXT,
    status TEXT,
    expected_table_count INTEGER,
    zone_count INTEGER,
    sheet_id TEXT,
    drive_folder_id TEXT,
    last_synced_at TEXT,
    validation_json TEXT,
    validated_at TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS tables (
    session_id TEXT,
    table_id TEXT,
    zone_id TEXT,
    display_order INTEGER,
    PRIMARY KEY (session_id, table_id)
);

CREATE TABLE IF NOT EXISTS submissions (
    submission_id TEXT PRIMARY KEY,
    session_id TEXT,
    row_key TEXT,
    table_id TEXT,
    zone_id TEXT,
    submitter TEXT,
    submitted_at TEXT,
    drive_file_id TEXT,
    mime_type TEXT,
    size INTEGER,
    photo_accessible INTEGER DEFAULT 0,
    validation_status TEXT,
    created_at TEXT,
    UNIQUE (session_id, row_key)
);

CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    table_id TEXT,
    version INTEGER,
    source TEXT,
    status TEXT,
    reason TEXT,
    confidence REAL,
    ai_json TEXT,
    model TEXT,
    submission_id TEXT,
    error_code TEXT,
    updated_by TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    type TEXT,
    session_id TEXT,
    status TEXT,
    completed INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0,
    failed_items TEXT DEFAULT '[]',
    params TEXT DEFAULT '{}',
    created_at TEXT,
    started_at TEXT,
    finished_at TEXT
);
"""


def get_db():
    """SQLite 연결 객체를 반환한다. 결과를 딕셔너리처럼 꺼낼 수 있도록 Row 팩토리를 설정한다."""
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    """서버 시작 시 테이블을 생성한다."""
    con = get_db()
    con.executescript(SCHEMA)
    con.commit()
    con.close()


def now():
    """현재 시각을 문자열(ISO 형식)로 반환한다."""
    return datetime.now().isoformat(timespec="seconds")


def new_id(prefix):
    """접두사 + 짧은 고유 ID를 만든다. (예: sub_a1b2c3d4)"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"
