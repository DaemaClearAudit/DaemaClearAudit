"""Session management and import of Google Form responses."""
import hmac
import json
import os
import re
import uuid
from datetime import date, datetime, timezone
from typing import Literal

from pydantic import AliasChoices

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, Response
from pydantic import BaseModel, Field, field_validator, model_validator
from . import google_sync, store

router = APIRouter()
TABLES = tuple(f'{z}-{n:02d}' for z in 'ABCD' for n in range(1, 5))

def normalize_table(zone, value):
    value = value.upper().replace(' ', '').replace('-', '')
    if value.isdigit():
        value = zone + value
    match = re.fullmatch(r'([A-D])0*([1-4])', value)
    if not match or match.group(1) != zone:
        raise ValueError('구역과 테이블 ID가 일치하지 않습니다')
    return f'{zone}-{int(match.group(2)):02d}'

def now():
    return datetime.now(timezone.utc).isoformat()

def authorize(authorization: str | None = Header(default=None)):
    secret = os.getenv('ADMIN_API_TOKEN', '')
    if not secret:
        raise HTTPException(503, '서버 관리자 인증 설정이 없습니다')
    if not authorization or not authorization.startswith('Bearer ') or not hmac.compare_digest(authorization[7:].encode('utf-8'), secret.encode('utf-8')):
        raise HTTPException(401, '관리자 인증이 필요합니다', headers={'WWW-Authenticate': 'Bearer'})

admin = [Depends(authorize)]

class TableDefinition(BaseModel):
    table_id: str
    zone_id: Literal['A', 'B', 'C', 'D']
    display_order: int = Field(ge=1, le=4)

class SessionCreate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    inspection_date: date | None = None
    started_at: datetime | None = None
    expected_table_count: Literal[16] = 16
    zone_count: Literal[4] = 4
    tables: list[TableDefinition] | None = None

    @model_validator(mode='after')
    def validate_session(self):
        if self.name is not None and not self.name.strip():
            raise ValueError('이름은 공백일 수 없습니다')
        if self.started_at is not None and self.started_at.utcoffset() is None:
            raise ValueError('시작 시각에는 시간대가 필요합니다')
        if self.tables is not None:
            ids = [normalize_table(t.zone_id, t.table_id) for t in self.tables]
            if len(ids) != 16 or set(ids) != set(TABLES):
                raise ValueError('A부터 D까지 16개의 서로 다른 테이블이 필요합니다')
            if any(t.display_order != int(t.table_id.replace('-', '')[-1]) for t in self.tables):
                raise ValueError('테이블 순서와 번호가 일치해야 합니다')
        if not self.name and not self.inspection_date:
            raise ValueError('회차 이름 또는 검사일이 필요합니다')
        return self

class SessionPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    inspection_date: date | None = None
    started_at: datetime | None = None
    status: Literal['DRAFT', 'OPEN'] | None = None
    sheet_id: str | None = Field(default=None, min_length=1, max_length=200)
    drive_folder_id: str | None = Field(default=None, min_length=1, max_length=200)

    @model_validator(mode='after')
    def validate_patch(self):
        if not self.model_fields_set:
            raise ValueError('수정할 항목을 지정하세요')
        if self.name is not None and not self.name.strip():
            raise ValueError('이름은 공백일 수 없습니다')
        if self.started_at is not None and self.started_at.utcoffset() is None:
            raise ValueError('시작 시각에는 시간대가 필요합니다')
        return self

class SyncRequest(BaseModel):
    session_id: str
    spreadsheet_id: str = Field(min_length=1, validation_alias=AliasChoices('spreadsheet_id', 'sheet_id'))
    drive_folder_id: str | None = None
    full_sync: bool = False
    sheet_range: str = Field(default='Form Responses 1!A:Z', min_length=1)
    # Values are exact column headings in the linked Google Sheet.
    columns: dict[str, str] = Field(default_factory=lambda: {
        'session_id': '검사 회차', 'zone': '본인 모둠', 'table_id': '본인 자리',
        'photo': '사진을 찍어주세요', 'submitted_at': '타임스탬프', 'submitter': '이메일 주소'})

class ValidateRequest(BaseModel):
    mode: Literal['full'] = 'full'
    auto_resolve: Literal[False] = False

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
    if row['status'] not in ('OPEN', 'DRAFT'):
        raise HTTPException(409, '종료된 회차는 변경할 수 없습니다')
    return row

def validation(db, session_id):
    rows = db.execute('SELECT table_id, COUNT(*) AS count FROM submissions WHERE session_id=? GROUP BY table_id', (session_id,)).fetchall()
    counts = {r['table_id']: r['count'] for r in rows}
    missing = [t for t in TABLES if t not in counts]
    duplicates = []
    for table in TABLES:
        if counts.get(table, 0) > 1:
            ids = [r['id'] for r in db.execute('SELECT id FROM submissions WHERE session_id=? AND table_id=? ORDER BY id', (session_id, table))]
            duplicates.append({'table_id': table, 'count': counts[table], 'submission_ids': ids})
    conflicts = [dict(r) for r in db.execute(
        'SELECT source_key,reason FROM sync_conflicts WHERE session_id=? ORDER BY source_key', (session_id,))]
    return {'session_id': session_id, 'expected': 16, 'expected_count': 16, 'received_count': sum(counts.values()),
            'submitted_tables': len(counts), 'missing_table_ids': missing, 'unmapped_submission_ids': [],
            'warnings': [f"{d['table_id']}에 중복 제출이 있습니다." for d in duplicates],
            'missing': missing, 'duplicates': duplicates, 'conflicts': conflicts,
            'valid': not missing and not duplicates and not conflicts}

def session_summary(db, row):
    result = dict(row)
    report = validation(db, row['id'])
    completed = db.execute("SELECT COUNT(*) FROM submissions WHERE session_id=? AND status='COMPLETED'", (row['id'],)).fetchone()[0]
    result.update(session_id=row['id'], expected_table_count=16, zone_count=4,
                  submitted_count=report['submitted_tables'], completed_count=completed,
                  last_updated_at=row['updated_at'] or row['created_at'],
                  can_close=row['status'] != 'CLOSED' and report['valid'] and completed == 16 and row['photos_verified'] == '1')
    return result

@router.post('/sessions', status_code=201, dependencies=admin)
def create_session(body: SessionCreate):
    sid = str(uuid.uuid4())
    with store.connection(write=True) as db:
        timestamp = now()
        day = body.inspection_date.isoformat() if body.inspection_date else timestamp[:10]
        started = body.started_at.isoformat() if body.started_at else None
        db.execute('INSERT INTO sessions (id,name,status,created_at,inspection_date,started_at,updated_at) VALUES (?,?,?,?,?,?,?)',
                   (sid, body.name.strip() if body.name else day, 'DRAFT', timestamp, day, started, timestamp))
        return session_summary(db, get_session(db, sid))

@router.get('/sessions', dependencies=admin)
def list_sessions(status: Literal['DRAFT', 'OPEN', 'CLOSED'] | None = None,
                  date_from: date | None = Query(default=None, alias='from'),
                  date_to: date | None = Query(default=None, alias='to'),
                  limit: int = Query(default=50, ge=1, le=100), cursor: str | None = None):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, '시작일은 종료일보다 늦을 수 없습니다')
    conditions, params = [], []
    if status:
        conditions.append('status=?')
        params.append(status)
    if date_from:
        conditions.append('COALESCE(inspection_date, substr(created_at,1,10)) >= ?')
        params.append(date_from.isoformat())
    if date_to:
        conditions.append('COALESCE(inspection_date, substr(created_at,1,10)) <= ?')
        params.append(date_to.isoformat())
    with store.connection() as db:
        if cursor:
            anchor = get_session(db, cursor)
            conditions.append('(created_at < ? OR (created_at = ? AND id < ?))')
            params.extend([anchor['created_at'], anchor['created_at'], anchor['id']])
        query = 'SELECT * FROM sessions'
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY created_at DESC,id DESC LIMIT ?'
        params.append(limit)
        return [session_summary(db, row) for row in db.execute(query, params)]

@router.get('/sessions/{session_id}', dependencies=admin)
def session_detail(session_id: str):
    with store.connection() as db:
        result = session_summary(db, get_session(db, session_id))
        result['validation'] = validation(db, session_id)
        return result

@router.patch('/sessions/{session_id}', dependencies=admin)
def update_session(session_id: str, body: SessionPatch):
    with store.connection(write=True) as db:
        open_session(db, session_id)
        updates = body.model_dump(exclude_unset=True, exclude_none=True, mode='json')
        if not updates:
            raise HTTPException(422, '수정할 항목을 지정하세요')
        if 'name' in updates:
            updates['name'] = updates['name'].strip()
        if 'drive_folder_id' in updates or 'sheet_id' in updates:
            updates['photos_verified'] = '0'
        updates['updated_at'] = now()
        clause = ','.join(f'{field}=?' for field in updates)
        db.execute(f'UPDATE sessions SET {clause} WHERE id=?', (*updates.values(), session_id))
        return session_summary(db, get_session(db, session_id))

@router.post('/sessions/{session_id}/close', dependencies=admin)
def close_session(session_id: str):
    with store.connection(write=True) as db:
        open_session(db, session_id)
        report = validation(db, session_id)
        if not report['valid']:
            raise HTTPException(409, '미제출, 중복 제출 또는 동기화 충돌이 있어 종료할 수 없습니다')
        if get_session(db, session_id)['photos_verified'] != '1':
            raise HTTPException(409, '사진 접근 검증을 먼저 완료해야 합니다')
        unfinished = db.execute("SELECT COUNT(*) FROM submissions WHERE session_id=? AND status != 'COMPLETED'", (session_id,)).fetchone()[0]
        if unfinished:
            raise HTTPException(409, '판독이 완료되지 않은 사진이 있습니다')
        db.execute("UPDATE sessions SET status='CLOSED',closed_at=?,updated_at=? WHERE id=?", (now(), now(), session_id))
        return session_summary(db, get_session(db, session_id))

@router.get('/sessions/{session_id}/submissions', dependencies=admin)
def submissions(session_id: str):
    with store.connection() as db:
        get_session(db, session_id)
        return [dict(r) for r in db.execute('SELECT * FROM submissions WHERE session_id=? ORDER BY created_at,id', (session_id,))]

@router.post('/sessions/{session_id}/submissions/validate', dependencies=admin)
def validate(session_id: str, body: ValidateRequest = ValidateRequest()):
    with store.connection() as db:
        session = get_session(db, session_id)
        if session['status'] == 'CLOSED':
            raise HTTPException(409, '종료된 회차는 검증할 수 없습니다')
        snapshot = [dict(r) for r in db.execute(
            'SELECT id,photo_id FROM submissions WHERE session_id=? ORDER BY id', (session_id,))]
        folder_id = session['drive_folder_id']
    inaccessible = []
    for item in snapshot:
        try:
            google_sync.photo_metadata(item['photo_id'], folder_id)
        except Exception:
            inaccessible.append(item['id'])
    with store.connection(write=True) as db:
        open_session(db, session_id)
        current = [dict(r) for r in db.execute(
            'SELECT id,photo_id FROM submissions WHERE session_id=? ORDER BY id', (session_id,))]
        if current != snapshot:
            raise HTTPException(409, '검증 중 제출이 변경되었습니다. 다시 검증하세요')
        report = validation(db, session_id)
        report['inaccessible_photo_submission_ids'] = inaccessible
        if inaccessible:
            report['warnings'].append('접근할 수 없거나 지원하지 않는 사진이 있습니다.')
        report['valid'] = report['valid'] and not inaccessible
        verified = report['valid'] and len(snapshot) == 16
        db.execute('UPDATE sessions SET photos_verified=?,updated_at=? WHERE id=?',
                   ('1' if verified else '0', now(), session_id))
        return report

@router.patch('/submissions/{submission_id}/status', dependencies=admin)
def update_status(submission_id: str, body: StatusPatch):
    with store.connection(write=True) as db:
        row = db.execute('SELECT * FROM submissions WHERE id=?', (submission_id,)).fetchone()
        if not row:
            raise HTTPException(404, '제출을 찾을 수 없습니다')
        open_session(db, row['session_id'])
        db.execute('UPDATE submissions SET status=?,verdict=?,reason=? WHERE id=?', (body.status, body.verdict, body.reason, submission_id))
        db.execute('UPDATE sessions SET updated_at=? WHERE id=?', (now(), row['session_id']))
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

def perform_sync(body: SyncRequest):
    required = {'session_id', 'zone', 'table_id', 'photo'}
    if not required.issubset(body.columns) or len(set(body.columns.values())) != len(body.columns):
        raise HTTPException(422, '필수 항목과 서로 다른 열 이름을 지정하세요')
    if not re.fullmatch(r"(?:'[^']+(?:''[^']*)*'|[^'!]+)!A(?::Z|1:Z)", body.sheet_range, re.IGNORECASE):
        raise HTTPException(422, '시트 범위는 헤더부터 읽도록 시트명!A:Z 형식이어야 합니다')
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
    prefix = f'{body.spreadsheet_id}:{body.sheet_range}:'
    with store.connection(write=True) as db:
        open_session(db, body.session_id)
        registered = db.execute('SELECT sheet_range FROM sheet_sources WHERE spreadsheet_id=?',
                                (body.spreadsheet_id,)).fetchone()
        if registered and registered['sheet_range'] != body.sheet_range:
            raise HTTPException(409, '등록된 시트 범위가 다릅니다. 중복 가져오기를 방지하기 위해 기존 범위를 사용하세요')
        if not registered:
            db.execute('INSERT INTO sheet_sources (spreadsheet_id,sheet_range) VALUES (?,?)',
                       (body.spreadsheet_id, body.sheet_range))
        # A response row must not silently disappear, move, or change after import.
        prior = db.execute('SELECT source_key,session_id,table_id,photo_id FROM submissions '
                           'WHERE session_id=? AND substr(source_key,1,?)=?',
                           (body.session_id, len(prefix), prefix)).fetchall()
        db.execute('DELETE FROM sync_conflicts WHERE session_id=? AND substr(source_key,1,?)=?',
                   (body.session_id, len(prefix), prefix))
        for old in prior:
            try:
                row_num = int(old['source_key'][len(prefix):])
                row = values[row_num - 1]
                def old_field(name):
                    idx = indices.get(name)
                    return str(row[idx]).strip() if idx is not None and idx < len(row) else ''
                zone = old_field('zone').upper()
                table = normalize_table(zone, old_field('table_id'))
                matches = (old_field('session_id') == old['session_id'] and zone in 'ABCD'
                           and len(zone) == 1 and table == old['table_id']
                           and table.startswith(zone)
                           and google_sync.drive_file_id(old_field('photo')) == old['photo_id'])
            except (IndexError, ValueError):
                matches = False
            if not matches:
                reason = '가져온 응답 행이 변경되거나 사라졌습니다. 원본을 확인하세요'
                db.execute('INSERT INTO sync_conflicts (source_key,session_id,reason) VALUES (?,?,?)',
                           (old['source_key'], old['session_id'], reason))
                rejected.append({'row': row_num, 'reason': reason})
        conflict_keys = {r['source_key'] for r in db.execute(
            'SELECT source_key FROM sync_conflicts WHERE session_id=?', (body.session_id,))}
        for row_num, row in enumerate(values[1:], start=2):
            def field(name):
                idx = indices.get(name)
                return str(row[idx]).strip() if idx is not None and idx < len(row) else ''
            if field('session_id') != body.session_id:
                continue
            try:
                zone = field('zone').upper().strip()
                table = normalize_table(zone, field('table_id'))
                if zone not in 'ABCD' or len(zone) != 1 or table not in TABLES or not table.startswith(zone):
                    raise ValueError('구역과 테이블 ID가 일치하지 않습니다')
                photo = google_sync.drive_file_id(field('photo'))
                if body.drive_folder_id:
                    try:
                        google_sync.photo_metadata(photo, body.drive_folder_id)
                    except ValueError:
                        raise
                    except Exception as exc:
                        raise HTTPException(502, 'Google Drive 사진 정보를 읽지 못했습니다') from exc
                key = f'{prefix}{row_num}'
                if key in conflict_keys:
                    continue
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
                reason = str(exc)
                rejected.append({'row': row_num, 'reason': reason})
                db.execute('INSERT OR REPLACE INTO sync_conflicts (source_key,session_id,reason) VALUES (?,?,?)',
                           (f'{prefix}{row_num}', body.session_id, reason))
        db.execute("UPDATE sessions SET last_synced_at=?,updated_at=?,sheet_id=?,drive_folder_id=COALESCE(?,drive_folder_id),photos_verified='0' WHERE id=?",
                   (now(), now(), body.spreadsheet_id, body.drive_folder_id, body.session_id))
        report = validation(db, body.session_id)
    return {'imported': accepted, 'already_imported': existing, 'rejected': rejected, 'validation': report}


def run_sync_job(job_id: str, body: SyncRequest):
    try:
        with store.connection(write=True) as db:
            db.execute("UPDATE jobs SET status='RUNNING',updated_at=? WHERE id=?", (now(), job_id))
        result = perform_sync(body)
        with store.connection(write=True) as db:
            db.execute("UPDATE jobs SET status='COMPLETED',updated_at=?,result=? WHERE id=?",
                       (now(), json.dumps(result, ensure_ascii=False), job_id))
    except Exception as exc:
        detail = str(exc.detail) if isinstance(exc, HTTPException) else '동기화 처리 중 오류가 발생했습니다'
        with store.connection(write=True) as db:
            db.execute("UPDATE jobs SET status='ERROR',updated_at=?,error=? WHERE id=?", (now(), detail, job_id))

@router.post('/integrations/google/sheets/sync', status_code=202, dependencies=admin)
def sync(body: SyncRequest, background_tasks: BackgroundTasks):
    required = {'session_id', 'zone', 'table_id', 'photo'}
    if not required.issubset(body.columns) or len(set(body.columns.values())) != len(body.columns):
        raise HTTPException(422, '필수 항목과 서로 다른 열 이름을 지정하세요')
    if not re.fullmatch(r"(?:'[^']+(?:''[^']*)*'|[^'!]+)!A(?::Z|1:Z)", body.sheet_range, re.IGNORECASE):
        raise HTTPException(422, '시트 범위는 헤더부터 읽도록 시트명!A:Z 형식이어야 합니다')
    job_id = 'job_sync_' + uuid.uuid4().hex
    timestamp = now()
    with store.connection(write=True) as db:
        open_session(db, body.session_id)
        registered = db.execute('SELECT sheet_range FROM sheet_sources WHERE spreadsheet_id=?',
                                (body.spreadsheet_id,)).fetchone()
        if registered and registered['sheet_range'] != body.sheet_range:
            raise HTTPException(409, '등록된 시트 범위가 다릅니다')
        db.execute("INSERT INTO jobs (id,session_id,status,accepted_at,updated_at) VALUES (?,?,'QUEUED',?,?)",
                   (job_id, body.session_id, timestamp, timestamp))
    background_tasks.add_task(run_sync_job, job_id, body)
    return {'job_id': job_id, 'session_id': body.session_id, 'status': 'QUEUED', 'accepted_at': timestamp}

@router.get('/jobs/{job_id}', dependencies=admin)
def job_status(job_id: str):
    with store.connection() as db:
        row = db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
        if not row:
            raise HTTPException(404, '작업을 찾을 수 없습니다')
        result = dict(row)
        if result['result']:
            result['result'] = json.loads(result['result'])
        return result
