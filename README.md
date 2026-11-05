# 자동 청소 검사 (Automatic Cleaning Inspection)

대덕소프트웨어마이스터고 인공지능 프로그래밍 프로젝트.
테이블 청소 상태를 사진으로 제출하면 AI가 판독해 점검한다.

## 구조

```
backend/    FastAPI 서버 (사진 업로드, AI 판독, 결과 저장)
frontend/   웹 클라이언트
```

## 백엔드 실행

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # 윈도우: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

http://127.0.0.1:8000/health 접속해서 `{"status":"ok"}` 나오면 정상.
API 문서는 http://127.0.0.1:8000/docs 에서 자동 생성된다.

## 작업 규칙

- `.venv/` 는 커밋하지 않는다. 패키지를 추가했으면 `pip freeze > requirements.txt` 로 목록만 갱신한다.
- 작업 전 `git pull`, 작업 후 `git add .` → `git commit` → `git push`.
- 커밋 메시지는 `feat:` / `fix:` / `chore:` / `docs:` 접두어를 붙인다.

## 검사 회차 및 Google Form 응답 서버

찬호 담당 범위는 회차 관리, Google Sheets 응답 가져오기, 제출 검증과 상태 저장입니다. 기존 `/inspect` 판독은 별도 담당자의 코드입니다. Google 연동은 관리자 계정의 설정과 실제 양식 수정이 필요합니다.

1. `backend/.env.example`을 `backend/.env`로 복사하고 `ADMIN_API_TOKEN`을 충분히 긴 임의 문자열로 설정합니다. 예: `python -c 'import secrets; print(secrets.token_urlsafe(32))'`. 외부에 공개하지 마세요.
2. Google Cloud에서 Sheets API와 Drive API를 활성화하고, 서비스 계정에 연결된 응답 시트와 사진 폴더의 **읽기** 권한을 부여합니다. 서비스 계정 파일 경로를 `GOOGLE_APPLICATION_CREDENTIALS`에 지정합니다. 인증 파일은 저장소에 올리지 않습니다. API 접근과 권한 설정은 프로젝트 담당자가 수행해야 합니다.
3. 실제 Form에 필수 **검사 회차** 질문을 추가하고, 서버에서 생성한 회차 ID를 제출자가 선택하게 연결해야 합니다. 현재 확인된 Form에는 해당 항목이 없어서 지금 상태로는 안전하게 회차를 구분할 수 없습니다. 기존 Form의 질문은 `본인 모둠`, `본인 자리`, `사진을 찍어주세요`입니다. 각 항목은 한 개씩만 선택하게 설정해야 합니다.
4. `cd backend && uvicorn main:app --reload`로 실행합니다. 관리자 API는 `Authorization: Bearer <ADMIN_API_TOKEN>`이 필요하고 `/health`는 인증이 필요 없습니다. `/docs`에서 API를 확인할 수 있습니다.
5. `POST /sessions`에 `inspection_date`, `started_at`, `expected_table_count`, `zone_count`, `tables`를 보내고 반환된 `session_id`를 Form 회차 값으로 사용합니다. `name`만 전달하는 초기 방식도 지원합니다. `POST /integrations/google/sheets/sync`에 `session_id`, `sheet_id`, `drive_folder_id`, `sheet_range`를 보냅니다. 응답의 `job_id`를 `GET /jobs/{job_id}`로 조회하면 동기화 결과나 오류를 확인할 수 있습니다. `full_sync` 설정과 관계없이 현재는 항상 전체 응답 행을 확인합니다. 기본 열 이름이 실제 응답 시트와 다르면 요청의 `columns`로 정확한 헤더를 지정합니다.
6. `GET /sessions/{id}/submissions`와 `POST /sessions/{id}/submissions/validate`에서 제출과 중복·미제출을 확인합니다. 검증 API는 Drive에서 모든 사진의 접근 권한, MIME 형식, 크기를 확인합니다. 각 제출은 `RECEIVED`, `PROCESSING`, `COMPLETED`, `ERROR` 상태를 가지며 `/submissions/{id}/status`에서 변경할 수 있습니다. `COMPLETED`에는 `verdict`(PASS/FAIL/REVIEW)와 `reason`이 필수입니다. 원본 사진은 인증된 `GET /submissions/{id}/photo`로 조회합니다.

동기화는 응답 시트가 **맨 위 행이 헤더인 추가 전용 시트**이며, 같은 범위 설정을 계속 사용한다는 전제에서 행 단위로 중복 입력을 방지합니다. 행 삭제·정렬·이동이나 범위 변경은 별도 이관 없이 하지 마세요. 한 테이블에 둘 이상 제출되면 삭제하거나 자동 선택하지 않고 중복으로 보고합니다. 미제출·중복·동기화 오류가 없고 사진 접근 검증을 통과했으며 모든 처리 상태가 `COMPLETED`일 때만 회차를 종료합니다. Google Drive 권한이나 원본 시트는 외부에서 바뀔 수 있으므로 종료 직전에 동기화와 검증을 다시 수행하세요. 현재 사진 다운로드 제한은 15 MiB이고 Form의 제한(100 MB)과 다르므로 운영 설정을 통일해야 합니다.

서버 테스트: `pip install pytest httpx` 후 프로젝트 루트에서 `python -m pytest -q backend/tests`.

동기화 작업은 현재 단일 서버 프로세스의 백그라운드 작업입니다. 여러 Uvicorn 워커를 쓰지 마세요. 서버가 작업 중 종료되면 재시작할 때 해당 작업을 ERROR로 표시하며 재시도가 필요합니다. `/inspect`도 관리자 인증이 필요합니다.
