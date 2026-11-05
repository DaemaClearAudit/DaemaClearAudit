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
    return client.post('/integrations/google/sheets/sync', json={
        'session_id': session, 'spreadsheet_id': 'sheet-id', 'sheet_range': '응답!A:Z'})

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
    assert body['validation']['duplicates'] == [{'table_id':'A1', 'count':2}]
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
