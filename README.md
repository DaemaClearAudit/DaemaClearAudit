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
