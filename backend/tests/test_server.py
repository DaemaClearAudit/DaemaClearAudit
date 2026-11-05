import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import app
from inspection_server import google_sync, store

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('ADMIN_API_TOKEN', 'test-secret')
    monkeypatch.setattr(store, 'DB_PATH', tmp_path / 'inspection.sqlite3')
    with TestClient(app, headers={'Authorization': 'Bearer test-secret'}) as c:
        yield c

def make_session(client):
    result = client.post('/sessions', json={'name': '점심 점검'})
    assert result.status_code == 201, result.text
    return result.json()['id']

def sheet(session, *rows):
    return [['검사 회차','본인 모둠','본인 자리','사진을 찍어주세요','타임스탬프','이메일 주소'],
            *[[session, zone, table, photo, '2026-11-05', 'student@dsm.hs.kr'] for zone, table, photo in rows]]

def sync(client, session):
    from types import SimpleNamespace
    result = client.post('/integrations/google/sheets/sync', json={
        'session_id': session, 'spreadsheet_id': 'sheet-id', 'sheet_range': '응답!A:Z'})
    if result.status_code != 202:
        return result
    job = client.get('/jobs/' + result.json()['job_id']).json()
    if job['status'] == 'ERROR':
        return SimpleNamespace(status_code=422, text=job['error'], json=lambda: job)
    assert job['status'] == 'COMPLETED', job
    return SimpleNamespace(status_code=200, text='', json=lambda: job['result'])

def test_authentication_fails_closed(client, monkeypatch):
    assert client.get('/health').status_code == 200
    assert client.get('/sessions', headers={'Authorization':'Bearer wrong'}).status_code == 401
    monkeypatch.delenv('ADMIN_API_TOKEN')
    assert client.get('/sessions').status_code == 503

def test_sync_is_idempotent_and_reports_duplicate_missing_invalid(client, monkeypatch):
    session = make_session(client)
    data = sheet(session, ('A','A1','https://drive.google.com/open?id=abcdefghijk'),
                 ('A','1','abcdefghijk2'), ('A','B2','abcdefghijk3'),
                 ('B','B1','https://evil.example/file/abcdefghijk4'))
    monkeypatch.setattr(google_sync, 'rows', lambda *args: data)
    first = sync(client, session)
    assert first.status_code == 200, first.text
    body = first.json()
    assert body['imported'] == 2 and len(body['rejected']) == 2
    assert body['validation']['duplicates'][0]['table_id'] == 'A-01'
    assert body['validation']['duplicates'][0]['count'] == 2
    assert len(body['validation']['duplicates'][0]['submission_ids']) == 2
    assert len(body['validation']['missing']) == 15
    second = sync(client, session).json()
    assert second['imported'] == 0 and second['already_imported'] == 2
    assert len(client.get(f'/sessions/{session}/submissions').json()) == 2
    assert client.post(f'/sessions/{session}/close').status_code == 409
    data[1][3] = 'changedfileid1234'
    assert '변경' in sync(client, session).json()['rejected'][0]['reason']

def test_full_round_persists_processing_states_and_close(client, monkeypatch):
    session = make_session(client)
    data = sheet(session, *[(zone, f'{zone}{n}', f'file{zone}{n}abcdefghi') for zone in 'ABCD' for n in range(1,5)])
    monkeypatch.setattr(google_sync, 'rows', lambda *args: data)
    assert sync(client, session).json()['validation']['valid']
    items = client.get(f'/sessions/{session}/submissions').json()
    assert len(items) == 16
    monkeypatch.setattr(google_sync, 'photo_metadata', lambda *args: {'mimeType': 'image/jpeg'})
    assert client.post(f'/sessions/{session}/submissions/validate', json={'mode':'full','auto_resolve':False}).json()['valid']
    assert client.post(f'/sessions/{session}/close').status_code == 409
    assert client.patch(f"/submissions/{items[0]['id']}/status", json={'status':'COMPLETED'}).status_code == 422
    for item in items:
        assert client.patch(f"/submissions/{item['id']}/status", json={'status':'COMPLETED', 'verdict':'PASS', 'reason':'깨끗함'}).status_code == 200
    assert client.post(f'/sessions/{session}/close').json()['status'] == 'CLOSED'
    assert sync(client, session).status_code == 409
    assert client.patch(f"/submissions/{items[0]['id']}/status", json={'status':'ERROR'}).status_code == 409
    assert client.get(f'/sessions/{session}').json()['status'] == 'CLOSED'

def test_photo_retrieval_and_failures(client, monkeypatch):
    session = make_session(client)
    monkeypatch.setattr(google_sync, 'rows', lambda *args: sheet(session, ('A','A1','abcdefghijk')))
    sync(client, session)
    sid = client.get(f'/sessions/{session}/submissions').json()[0]['id']
    monkeypatch.setattr(google_sync, 'photo', lambda file_id: (b'abc', 'image/jpeg'))
    response = client.get(f'/submissions/{sid}/photo')
    assert response.content == b'abc' and response.headers['content-type'] == 'image/jpeg'
    assert response.headers['cache-control'] == 'private, no-store'
    assert client.get('/submissions/unknown/photo').status_code == 404

def test_unknown_session_and_missing_sheet_columns(client, monkeypatch):
    assert client.get('/sessions/nonexistent').status_code == 404
    session = make_session(client)
    monkeypatch.setattr(google_sync, 'rows', lambda *args: [['구역'], ['A']])
    assert sync(client, session).status_code == 422
    assert client.get(f'/sessions/{session}/submissions').json() == []


def test_changed_or_deleted_rows_block_close_until_resolved(client, monkeypatch):
    session = make_session(client)
    data = sheet(session, *[(z, f'{z}{n}', f'file{z}{n}abcdefghi') for z in 'ABCD' for n in range(1, 5)])
    monkeypatch.setattr(google_sync, 'rows', lambda *args: data)
    assert sync(client, session).json()['validation']['valid']
    items = client.get(f'/sessions/{session}/submissions').json()
    for item in items:
        assert client.patch(f"/submissions/{item['id']}/status", json={
            'status': 'COMPLETED', 'verdict': 'PASS', 'reason': '깨끗함'}).status_code == 200
    removed = data.pop()
    report = sync(client, session).json()['validation']
    assert not report['valid'] and len(report['conflicts']) == 1
    assert client.post(f'/sessions/{session}/close').status_code == 409
    data.append(removed)
    assert sync(client, session).json()['validation']['valid']
    monkeypatch.setattr(google_sync, 'photo_metadata', lambda *args: {'mimeType': 'image/jpeg'})
    assert client.post(f'/sessions/{session}/submissions/validate').json()['valid']
    assert client.post(f'/sessions/{session}/close').status_code == 200


def test_rejected_rows_block_closing_and_range_cannot_change(client, monkeypatch):
    session = make_session(client)
    data = sheet(session, *[(z, f'{z}{n}', f'file{z}{n}abcdefghi') for z in 'ABCD' for n in range(1, 5)])
    data.append([session, 'A', '1', 'https://invalid.example/', '', ''])
    monkeypatch.setattr(google_sync, 'rows', lambda *args: data)
    result = sync(client, session).json()
    assert len(result['rejected']) == 1 and not result['validation']['valid']
    data.pop()
    assert sync(client, session).json()['validation']['valid']
    res = client.post('/integrations/google/sheets/sync', json={
        'session_id': session, 'spreadsheet_id': 'sheet-id', 'sheet_range': '응답!A1:Z'})
    assert res.status_code == 409
    res = client.post('/integrations/google/sheets/sync', json={
        'session_id': session, 'spreadsheet_id': 'sheet-id', 'sheet_range': '응답!A2:Z'})
    assert res.status_code == 422


def test_concurrent_sync_is_idempotent(client, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    session = make_session(client)
    data = sheet(session, ('A', 'A1', 'abcdefghijk'))
    monkeypatch.setattr(google_sync, 'rows', lambda *args: data)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: sync(client, session), range(2)))
    assert [r.status_code for r in responses] == [200, 200]
    assert sorted(r.json()['imported'] for r in responses) == [0, 1]
    assert len(client.get(f'/sessions/{session}/submissions').json()) == 1


def test_documented_create_and_canonical_table_ids(client, monkeypatch):
    tables = [{'table_id': f'{zone}-{n:02d}', 'zone_id': zone, 'display_order': n}
              for zone in 'ABCD' for n in range(1, 5)]
    response = client.post('/sessions', json={'inspection_date': '2026-11-05',
        'started_at': '2026-11-05T11:00:00+09:00', 'expected_table_count': 16,
        'zone_count': 4, 'tables': tables})
    assert response.status_code == 201, response.text
    session = response.json()['session_id']
    assert response.json()['status'] == 'DRAFT'
    assert response.json()['expected_table_count'] == 16
    monkeypatch.setattr(google_sync, 'rows', lambda *args: sheet(session, ('A','A-01','abcdefghijk')))
    assert sync(client, session).json()['imported'] == 1
    assert client.get(f'/sessions/{session}/submissions').json()[0]['table_id'] == 'A-01'
    bad = client.post('/sessions', json={'inspection_date': '2026-11-05', 'tables': tables[:-1]})
    assert bad.status_code == 422
    assert client.patch(f'/sessions/{session}', json={'status':'COMPLETED'}).status_code == 422
    assert client.patch(f'/sessions/{session}', json={'inspection_date':'2026-11-06'}).json()['inspection_date'] == '2026-11-06'


def test_documented_sync_creates_job_and_checks_drive_folder(client, monkeypatch):
    session = make_session(client)
    monkeypatch.setattr(google_sync, 'rows', lambda *args: sheet(session, ('A','1','abcdefghijk')))
    calls = []
    monkeypatch.setattr(google_sync, 'photo_metadata', lambda photo_id, folder_id: calls.append((photo_id, folder_id)))
    response = client.post('/integrations/google/sheets/sync', json={
        'session_id': session, 'sheet_id': 'sheet-id', 'sheet_range': '응답!A:Z',
        'drive_folder_id': 'folder-id', 'full_sync': False})
    assert response.status_code == 202 and response.json()['status'] == 'QUEUED'
    job = client.get('/jobs/' + response.json()['job_id']).json()
    assert job['status'] == 'COMPLETED' and job['result']['imported'] == 1
    assert calls == [('abcdefghijk', 'folder-id')]
    assert client.get('/jobs/not-found').status_code == 404


def test_google_failure_is_recorded_without_leaking_exception(client, monkeypatch):
    session = make_session(client)
    def fail(*args):
        raise RuntimeError('private-credential')
    monkeypatch.setattr(google_sync, 'rows', fail)
    queued = client.post('/integrations/google/sheets/sync', json={
        'session_id': session, 'sheet_id': 'sheet-id', 'sheet_range': '응답!A:Z'})
    assert queued.status_code == 202
    job = client.get('/jobs/' + queued.json()['job_id']).json()
    assert job['status'] == 'ERROR' and 'private-credential' not in job['error']


def test_inaccessible_photos_fail_full_validation(client, monkeypatch):
    session = make_session(client)
    monkeypatch.setattr(google_sync, 'rows', lambda *args: sheet(session, ('A','1','abcdefghijk')))
    assert sync(client, session).status_code == 200
    def deny(*args):
        raise RuntimeError('private error')
    monkeypatch.setattr(google_sync, 'photo_metadata', deny)
    report = client.post(f'/sessions/{session}/submissions/validate', json={'mode':'full','auto_resolve':False}).json()
    assert not report['valid'] and len(report['inaccessible_photo_submission_ids']) == 1
    assert 'private error' not in str(report)
    assert client.post(f'/sessions/{session}/close').status_code == 409
    assert client.post(f'/sessions/{session}/submissions/validate', json={'auto_resolve':True}).status_code == 422


def test_restart_marks_interrupted_job_as_error(tmp_path, monkeypatch):
    monkeypatch.setenv('ADMIN_API_TOKEN', 'test-secret')
    monkeypatch.setattr(store, 'DB_PATH', tmp_path / 'inspection.sqlite3')
    with TestClient(app, headers={'Authorization': 'Bearer test-secret'}) as c:
        session = make_session(c)
        with store.connection(write=True) as db:
            db.execute("INSERT INTO jobs (id,session_id,status,accepted_at,updated_at) VALUES (?,?, 'RUNNING','t','t')", ('interrupted', session))
    with TestClient(app, headers={'Authorization': 'Bearer test-secret'}) as c:
        assert c.get('/jobs/interrupted').json()['status'] == 'ERROR'


def test_legacy_inspect_cannot_run_without_authentication(client):
    response = client.post('/inspect', headers={'Authorization': 'Bearer bad'},
                           files={'file': ('photo.jpg', b'image', 'image/jpeg')})
    assert response.status_code == 401


def test_changed_folder_invalidates_photo_verification(client, monkeypatch):
    session = make_session(client)
    monkeypatch.setattr(google_sync, 'rows', lambda *args: sheet(session, *[
        (z, f'{z}{n}', f'file{z}{n}abcdefghi') for z in 'ABCD' for n in range(1, 5)]))
    monkeypatch.setattr(google_sync, 'photo_metadata', lambda *args: {'mimeType': 'image/jpeg'})
    sync(client, session)
    assert client.post(f'/sessions/{session}/submissions/validate').json()['valid']
    for item in client.get(f'/sessions/{session}/submissions').json():
        client.patch(f"/submissions/{item['id']}/status", json={'status':'COMPLETED','verdict':'PASS','reason':'정상'})
    assert client.get(f'/sessions/{session}').json()['can_close']
    assert client.patch(f'/sessions/{session}', json={'drive_folder_id':'new-folder'}).status_code == 200
    assert not client.get(f'/sessions/{session}').json()['can_close']
    assert client.post(f'/sessions/{session}/close').status_code == 409


def test_session_list_filters_and_cursor(client):
    ids = []
    for day in ('2026-11-03', '2026-11-04', '2026-11-05'):
        res = client.post('/sessions', json={'inspection_date': day})
        ids.append(res.json()['session_id'])
    filtered = client.get('/sessions', params={'from':'2026-11-04', 'to':'2026-11-05', 'status':'DRAFT'}).json()
    assert {row['session_id'] for row in filtered} == set(ids[1:])
    first = client.get('/sessions', params={'limit': 1}).json()
    second = client.get('/sessions', params={'limit': 1, 'cursor':first[0]['session_id']}).json()
    assert first[0]['session_id'] != second[0]['session_id']
    assert client.get('/sessions', params={'from':'2026-11-05', 'to':'2026-11-04'}).status_code == 422
