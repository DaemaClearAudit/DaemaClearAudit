"""Session management and import of Google Form responses."""
import hmac
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, Field, field_validator, model_validator
from . import google_sync, store

router = APIRouter()
TABLES = tuple(f'{z}{n}' for z in 'ABCD' for n in range(1, 5))

def now():
    return datetime.now(timezone.utc).isoformat()

def authorize(authorization: str | None = Header(default=None)):
    secret = os.getenv('ADMIN_API_TOKEN', '')
    if not secret:
        raise HTTPException(503, '서버 관리자 인증 설정이 없습니다')
    if not authorization or not authorization.startswith('Bearer ') or not hmac.compare_digest(authorization[7:], secret):
        raise HTTPException(401, '관리자 인증이 필요합니다', headers={'WWW-Authenticate': 'Bearer'})

admin = [Depends(authorize)]

class SessionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)

    @field_validator('name')
    @classmethod
    def nonblank_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('이름은 공백일 수 없습니다')
        return value

class SessionPatch(SessionCreate):
    pass

class SyncRequest(BaseModel):
    session_id: str
    spreadsheet_id: str = Field(min_length=1)
    sheet_range: str = Field(default='Form Responses 1!A:Z', min_length=1)
    # Values are exact column headings in the linked Google Sheet.
    columns: dict[str, str] = Field(default_factory=lambda: {
        'session_id': '검사 회차', 'zone': '본인 모둠', 'table_id': '본인 자리',
        'photo': '사진을 찍어주세요', 'submitted_at': '타임스탬프', 'submitter': '이메일 주소'})

class StatusPatch(BaseModel):
    status: Literal['RECEIVED', 'PROCESSING', 'COMPLETED', 'ERROR']
    verdict: Literal['PASS', 'FAIL', 'REVIEW'] | None = None
    reason: str | None = Field(default=None, max_length=2000)

    @model_validator(mode='after')
    def require_result(self):
        if self.status == 'COMPLETED' and (not self.verdict or not self.reason or not self.reason.strip()):
            raise ValueError('완료 상태에는 판정과 사유가 필요합니다')
        if self.status != 'COMPLETED' and (self.verdict is not None or self.reason is not None):
            raise ValueError('판정과 사유는 완료 상태에서만 지정합니다')
        return self

def get_session(db, session_id):
    row = db.execute('SELECT * FROM sessions WHERE id=?', (session_id,)).fetchone()
    if not row:
        raise HTTPException(404, '검사 회차를 찾을 수 없습니다')
    return row

def open_session(db, session_id):
    row = get_session(db, session_id)
    if row['status'] != 'OPEN':
        raise HTTPException(409, '종료된 회차는 변경할 수 없습니다')
    return row

def validation(db, session_id):
    rows = db.execute('SELECT table_id, COUNT(*) AS count FROM submissions WHERE session_id=? GROUP BY table_id', (session_id,)).fetchall()
    counts = {r['table_id']: r['count'] for r in rows}
    missing = [t for t in TABLES if t not in counts]
    duplicates = [{'table_id': t, 'count': counts[t]} for t in TABLES if counts.get(t, 0) > 1]
    return {'session_id': session_id, 'expected': 16, 'submitted_tables': len(counts),
            'missing': missing, 'duplicates': duplicates, 'valid': not missing and not duplicates}

@router.post('/sessions', status_code=201, dependencies=admin)
def create_session(body: SessionCreate):
    sid = str(uuid.uuid4())
    with store.connection() as db:
        db.execute('INSERT INTO sessions (id,name,created_at) VALUES (?,?,?)', (sid, body.name.strip(), now()))
        return dict(get_session(db, sid))

@router.get('/sessions', dependencies=admin)
def list_sessions():
    with store.connection() as db:
        return [dict(r) for r in db.execute('SELECT * FROM sessions ORDER BY created_at DESC')]

@router.get('/sessions/{session_id}', dependencies=admin)
def session_detail(session_id: str):
    with store.connection() as db:
        result = dict(get_session(db, session_id))
        result['validation'] = validation(db, session_id)
        return result

@router.patch('/sessions/{session_id}', dependencies=admin)
def update_session(session_id: str, body: SessionPatch):
    with store.connection() as db:
        open_session(db, session_id)
        db.execute('UPDATE sessions SET name=? WHERE id=?', (body.name.strip(), session_id))
        return dict(get_session(db, session_id))

@router.post('/sessions/{session_id}/close', dependencies=admin)
def close_session(session_id: str):
    with store.connection() as db:
        open_session(db, session_id)
        report = validation(db, session_id)
        if not report['valid']:
            raise HTTPException(409, '미제출 또는 중복 제출이 있어 종료할 수 없습니다')
        unfinished = db.execute("SELECT COUNT(*) FROM submissions WHERE session_id=? AND status != 'COMPLETED'", (session_id,)).fetchone()[0]
        if unfinished:
            raise HTTPException(409, '판독이 완료되지 않은 사진이 있습니다')
        db.execute("UPDATE sessions SET status='CLOSED',closed_at=? WHERE id=?", (now(), session_id))
        return dict(get_session(db, session_id))

@router.get('/sessions/{session_id}/submissions', dependencies=admin)
def submissions(session_id: str):
    with store.connection() as db:
        get_session(db, session_id)
        return [dict(r) for r in db.execute('SELECT * FROM submissions WHERE session_id=? ORDER BY created_at,id', (session_id,))]

@router.post('/sessions/{session_id}/submissions/validate', dependencies=admin)
def validate(session_id: str):
    with store.connection() as db:
        get_session(db, session_id)
        return validation(db, session_id)

@router.patch('/submissions/{submission_id}/status', dependencies=admin)
def update_status(submission_id: str, body: StatusPatch):
    with store.connection() as db:
        row = db.execute('SELECT * FROM submissions WHERE id=?', (submission_id,)).fetchone()
        if not row:
            raise HTTPException(404, '제출을 찾을 수 없습니다')
        open_session(db, row['session_id'])
        db.execute('UPDATE submissions SET status=?,verdict=?,reason=? WHERE id=?', (body.status, body.verdict, body.reason, submission_id))
        return dict(db.execute('SELECT * FROM submissions WHERE id=?', (submission_id,)).fetchone())

@router.get('/submissions/{submission_id}/photo', dependencies=admin)
def get_photo(submission_id: str):
    with store.connection() as db:
        row = db.execute('SELECT photo_id FROM submissions WHERE id=?', (submission_id,)).fetchone()
        if not row:
            raise HTTPException(404, '제출을 찾을 수 없습니다')
    try:
        data, mime = google_sync.photo(row['photo_id'])
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, 'Google Drive에서 사진을 가져오지 못했습니다') from exc
    return Response(content=data, media_type=mime, headers={'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff'})

@router.post('/integrations/google/sheets/sync', dependencies=admin)
def sync(body: SyncRequest):
    required = {'session_id', 'zone', 'table_id', 'photo'}
    if not required.issubset(body.columns) or len(set(body.columns.values())) != len(body.columns):
        raise HTTPException(422, '필수 항목과 서로 다른 열 이름을 지정하세요')
    with store.connection() as db:
        open_session(db, body.session_id)
    try:
        values = google_sync.rows(body.spreadsheet_id, body.sheet_range)
    except Exception as exc:
        raise HTTPException(502, 'Google Sheets 응답을 읽지 못했습니다. 권한과 설정을 확인하세요') from exc
    if not values:
        raise HTTPException(422, '응답 시트가 비어 있습니다')
    headings = values[0]
    if len(set(headings)) != len(headings):
        raise HTTPException(422, '시트 열 이름이 중복되었습니다')
    missing = [body.columns[k] for k in required if body.columns[k] not in headings]
    if missing:
        raise HTTPException(422, f'필수 열이 없습니다: {", ".join(missing)}')
    indices = {k: headings.index(v) for k, v in body.columns.items() if v in headings}
    accepted = 0
    existing = 0
    rejected = []
    with store.connection() as db:
        open_session(db, body.session_id)
        for row_num, row in enumerate(values[1:], start=2):
            def field(name):
                idx = indices.get(name)
                return str(row[idx]).strip() if idx is not None and idx < len(row) else ''
            if field('session_id') != body.session_id:
                continue
            try:
                zone = field('zone').upper().strip()
                table = field('table_id').upper().replace(' ', '').replace('-', '')
                if table.isdigit():
                    table = zone + table
                if zone not in 'ABCD' or len(zone) != 1 or table not in TABLES or not table.startswith(zone):
                    raise ValueError('구역과 테이블 ID가 일치하지 않습니다')
                photo = google_sync.drive_file_id(field('photo'))
                # Row location is stable only while the form response sheet is append-only.
                key = f'{body.spreadsheet_id}:{body.sheet_range}:{row_num}'
                previous = db.execute('SELECT session_id,table_id,photo_id FROM submissions WHERE source_key=?', (key,)).fetchone()
                if previous:
                    if (previous['session_id'], previous['table_id'], previous['photo_id']) != (body.session_id, table, photo):
                        raise ValueError('기존에 가져온 응답이 변경되었습니다. 관리자가 확인해야 합니다')
                    existing += 1
                    continue
                db.execute('INSERT INTO submissions (id,session_id,table_id,photo_id,source_key,submitted_at,submitter,created_at) VALUES (?,?,?,?,?,?,?,?)',
                           (str(uuid.uuid4()), body.session_id, table, photo, key, field('submitted_at'), field('submitter'), now()))
                accepted += 1
            except ValueError as exc:
                rejected.append({'row': row_num, 'reason': str(exc)})
        report = validation(db, body.session_id)
    return {'imported': accepted, 'already_imported': existing, 'rejected': rejected, 'validation': report}
