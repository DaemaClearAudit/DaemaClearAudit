import os
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def get_session():
    """서비스 계정 JSON 파일로 Google API 호출용 세션을 만든다."""
    key_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    if not key_file or not os.path.isfile(key_file):
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_FILE 환경변수가 설정되지 않았습니다.")
    creds = service_account.Credentials.from_service_account_file(key_file, scopes=SCOPES)
    return AuthorizedSession(creds)


def read_sheet(sheet_id: str) -> list:
    """Google Sheets의 첫 번째 시트 전체 데이터를 2차원 리스트로 읽어온다."""
    session = get_session()
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/A1:ZZ"
    resp = session.get(url)
    resp.raise_for_status()
    return resp.json().get("values", [])


def file_meta(file_id: str):
    """Google Drive 파일의 정보(id, mimeType, size)를 가져온다. 접근 불가면 None을 반환한다."""
    session = get_session()
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}"
    resp = session.get(url, params={"fields": "id,mimeType,size", "supportsAllDrives": "true"})
    if resp.status_code != 200:
        return None
    return resp.json()


def download(file_id: str) -> bytes:
    """Google Drive에서 원본 사진 바이트를 다운로드한다."""
    session = get_session()
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}"
    resp = session.get(url, params={"alt": "media", "supportsAllDrives": "true"})
    resp.raise_for_status()
    return resp.content
