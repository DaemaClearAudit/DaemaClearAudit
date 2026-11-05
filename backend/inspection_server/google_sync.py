"""Read-only Google Sheets and Drive adapter; no calls are made at import time."""
import os
import re
from urllib.parse import parse_qs, urlparse

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly',
          'https://www.googleapis.com/auth/drive.readonly']
FILE_ID = re.compile(r'^[A-Za-z0-9_-]{10,}$')

def drive_file_id(value: str) -> str:
    value = value.strip()
    if FILE_ID.fullmatch(value):
        return value
    url = urlparse(value)
    if url.scheme != 'https' or url.hostname not in {'drive.google.com', 'docs.google.com'}:
        raise ValueError('사진은 Google Drive 파일 링크 하나여야 합니다')
    candidates = parse_qs(url.query).get('id', [])
    parts = url.path.split('/')
    if 'd' in parts and parts.index('d') + 1 < len(parts):
        candidates.append(parts[parts.index('d') + 1])
    if len(set(candidates)) != 1 or not FILE_ID.fullmatch(candidates[0]):
        raise ValueError('Google Drive 파일 ID를 확인할 수 없습니다')
    return candidates[0]

def service(name, version):
    import google.auth
    from googleapiclient.discovery import build
    credentials, _ = google.auth.default(scopes=SCOPES)
    return build(name, version, credentials=credentials, cache_discovery=False)

def rows(spreadsheet_id: str, sheet_range: str):
    return service('sheets', 'v4').spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=sheet_range).execute().get('values', [])

def photo(file_id):
    from googleapiclient.http import MediaIoBaseDownload
    import io
    drive = service('drive', 'v3')
    meta = drive.files().get(fileId=file_id, fields='mimeType,size', supportsAllDrives=True).execute()
    mime = meta.get('mimeType', '')
    if mime not in {'image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif'}:
        raise ValueError('지원하지 않는 사진 형식입니다')
    if int(meta.get('size', '0')) > 15 * 1024 * 1024:
        raise ValueError('사진 크기가 제한을 초과했습니다')
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, drive.files().get_media(fileId=file_id, supportsAllDrives=True))
    done = False
    while not done:
        _, done = downloader.next_chunk()
        if buffer.tell() > 15 * 1024 * 1024:
            raise ValueError('사진 크기가 제한을 초과했습니다')
    return buffer.getvalue(), mime
