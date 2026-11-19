import json
import time
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

load_dotenv()

import db
import google_api
import jobs

# 서버 시작할 때 DB 테이블 생성
db.init_db()

app = FastAPI(title="Automatic Cleaning Inspection")

# 모든 출처(프론트엔드)에서 API 호출 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------- 요청 바디 모델 (Pydantic)

class SessionCreate(BaseModel):
    inspection_date: str
    started_at: str | None = None
    expected_table_count: int = 16
    zone_count: int = 4
    tables: list[dict] | None = None
    sheet_id: str | None = None
    drive_folder_id: str | None = None


class SessionPatch(BaseModel):
    inspection_date: str | None = None
    started_at: str | None = None
    status: str | None = None
    sheet_id: str | None = None
    drive_folder_id: str | None = None


class SyncInput(BaseModel):
    session_id: str
    sheet_id: str | None = None
    drive_folder_id: str | None = None
    full_sync: bool = False


class ValidateInput(BaseModel):
    mode: str = "full"
    auto_resolve: bool = False


class ProcessInput(BaseModel):
    table_ids: list[str] = []
    force: bool = False


class ReprocessInput(BaseModel):
    reason: str
    force: bool = False


class ManualResultInput(BaseModel):
    status: str  # PASS, FAIL, REVIEW
    reason: str
    result_version: int | None = None


# ---------------------------------------------------------------- 공통 조회 도우미 함수

def get_session_or_404(con, session_id: str) -> dict:
    """회차 정보를 가져오고, 없으면 404 에러를 낸다."""
    row = con.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="검사 회차를 찾을 수 없습니다.")
    return dict(row)


def get_table_rows(con, session_id: str) -> list:
    """회차의 모든 테이블 목록과 현재 판정 결과를 합쳐서 반환한다."""
    latest = jobs.get_latest_results(con, session_id)

    valid_subs = {}
    sub_rows = con.execute(
        "SELECT * FROM submissions WHERE session_id=? AND validation_status='VALID'",
        (session_id,),
    ).fetchall()
    for s in sub_rows:
        valid_subs[s["table_id"]] = dict(s)

    tables = con.execute(
        "SELECT * FROM tables WHERE session_id=? ORDER BY display_order",
        (session_id,),
    ).fetchall()

    result = []
    for t in tables:
        tid = t["table_id"]
        res = latest.get(tid)
        sub = valid_subs.get(tid)
        sub_id = sub["submission_id"] if sub else (res["submission_id"] if res else None)

        result.append({
            "table_id": tid,
            "zone_id": t["zone_id"],
            "table_number": int(tid.split("-")[1]),
            "status": res["status"] if res else "PENDING",
            "source": res["source"] if res else None,
            "confidence": res["confidence"] if res else None,
            "image_url": f"/api/v1/submissions/{sub_id}/photo" if sub_id else None,
            "submission_id": sub_id,
            "submitted_at": sub["submitted_at"] if sub else None,
            "result_version": res["version"] if res else 0,
        })
    return result


def count_statuses(rows: list) -> dict:
    """상태별(pass, review, fail, error, pending) 테이블 개수를 센다."""
    summary = {"pass": 0, "review": 0, "fail": 0, "error": 0, "pending": 0}
    for r in rows:
        key = r["status"].lower()
        if key in summary:
            summary[key] += 1
    return summary


def make_session_summary(con, s: dict) -> dict:
    """회차 요약 정보를 만든다."""
    rows = get_table_rows(con, s["session_id"])
    sub_count = con.execute(
        "SELECT COUNT(*) FROM submissions WHERE session_id=?",
        (s["session_id"],),
    ).fetchone()[0]
    done_count = sum(1 for r in rows if r["status"] in ("PASS", "FAIL", "REVIEW"))

    return {
        "session_id": s["session_id"],
        "inspection_date": s["inspection_date"],
        "status": s["status"],
        "expected_table_count": s["expected_table_count"],
        "submitted_count": sub_count,
        "completed_count": done_count,
        "last_updated_at": s["updated_at"],
    }


# ---------------------------------------------------------------- 0. 상태 확인 (Health Check)

@app.get("/health")
@app.get("/api/v1/health")
def health():
    return {"status": "ok", "checked_at": db.now()}


# ---------------------------------------------------------------- F-01. 검사 회차 관리

@app.post("/api/v1/sessions", status_code=201)
def create_session(body: SessionCreate):
    con = db.get_db()

    # 오늘 날짜의 몇 번째 회차인지 계산해 ID 생성 (예: sess_20261118_001)
    date_clean = body.inspection_date.replace("-", "")
    count = con.execute("SELECT COUNT(*) FROM sessions WHERE inspection_date=?", (body.inspection_date,)).fetchone()[0]
    session_id = f"sess_{date_clean}_{count + 1:03d}"

    # 테이블 목록이 없으면 A-01 ~ D-04 (4구역 x 4테이블 = 16개) 자동 생성
    tables = body.tables
    if not tables:
        tables = []
        per_zone = body.expected_table_count // body.zone_count
        order = 1
        for z in range(body.zone_count):
            zone_letter = chr(65 + z)  # 65='A', 66='B', ...
            for num in range(1, per_zone + 1):
                tables.append({
                    "table_id": f"{zone_letter}-{num:02d}",
                    "zone_id": zone_letter,
                    "display_order": order,
                })
                order += 1

    now_str = db.now()
    con.execute(
        """INSERT INTO sessions (
            session_id, inspection_date, started_at, status,
            expected_table_count, zone_count, sheet_id, drive_folder_id, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (session_id, body.inspection_date, body.started_at, "DRAFT",
         body.expected_table_count, body.zone_count, body.sheet_id, body.drive_folder_id, now_str, now_str),
    )

    for t in tables:
        con.execute(
            "INSERT INTO tables VALUES (?, ?, ?, ?)",
            (session_id, t["table_id"], t["zone_id"], t["display_order"]),
        )

    con.commit()
    summary = make_session_summary(con, get_session_or_404(con, session_id))
    con.close()
    return summary


@app.get("/api/v1/sessions")
def list_sessions(status: str | None = None):
    con = db.get_db()
    if status:
        rows = con.execute(
            "SELECT * FROM sessions WHERE status=? ORDER BY inspection_date DESC, session_id DESC",
            (status,),
        ).fetchall()
    else:
        rows = con.execute("SELECT * FROM sessions ORDER BY inspection_date DESC, session_id DESC").fetchall()

    items = [make_session_summary(con, dict(r)) for r in rows]
    con.close()
    return {"items": items, "next_cursor": None}


@app.get("/api/v1/sessions/{session_id}")
def session_detail(session_id: str):
    con = db.get_db()
    s = get_session_or_404(con, session_id)
    summary = make_session_summary(con, s)
    table_count = con.execute("SELECT COUNT(*) FROM tables WHERE session_id=?", (session_id,)).fetchone()[0]
    con.close()

    return {
        **summary,
        "started_at": s["started_at"],
        "zone_count": s["zone_count"],
        "table_count": table_count,
        "sheet_id": s["sheet_id"],
        "drive_folder_id": s["drive_folder_id"],
        "last_synced_at": s["last_synced_at"],
        "validation": json.loads(s["validation_json"]) if s["validation_json"] else None,
        "validated_at": s["validated_at"],
        "can_close": s["status"] != "CLOSED",
        "close_blockers": [],
        "created_at": s["created_at"],
    }


@app.patch("/api/v1/sessions/{session_id}")
def update_session(session_id: str, body: SessionPatch):
    con = db.get_db()
    s = get_session_or_404(con, session_id)

    inspection_date = body.inspection_date if body.inspection_date is not None else s["inspection_date"]
    started_at = body.started_at if body.started_at is not None else s["started_at"]
    status = body.status if body.status is not None else s["status"]
    sheet_id = body.sheet_id if body.sheet_id is not None else s["sheet_id"]
    drive_folder_id = body.drive_folder_id if body.drive_folder_id is not None else s["drive_folder_id"]

    con.execute(
        """UPDATE sessions
           SET inspection_date=?, started_at=?, status=?, sheet_id=?, drive_folder_id=?, updated_at=?
           WHERE session_id=?""",
        (inspection_date, started_at, status, sheet_id, drive_folder_id, db.now(), session_id),
    )
    con.commit()
    con.close()
    return session_detail(session_id)


@app.post("/api/v1/sessions/{session_id}/close")
def close_session(session_id: str):
    con = db.get_db()
    get_session_or_404(con, session_id)
    con.execute("UPDATE sessions SET status='CLOSED', updated_at=? WHERE session_id=?", (db.now(), session_id))
    con.commit()
    summary = make_session_summary(con, get_session_or_404(con, session_id))
    con.close()
    return summary


# ---------------------------------------------------------------- F-02 & F-03. 제출 동기화 및 검증

@app.post("/api/v1/integrations/google/sheets/sync", status_code=202)
def sync_sheet(body: SyncInput, bg: BackgroundTasks):
    con = db.get_db()
    s = get_session_or_404(con, body.session_id)
    sheet_id = body.sheet_id or s["sheet_id"]
    if not sheet_id:
        con.close()
        raise HTTPException(status_code=400, detail="sheet_id가 필요합니다.")

    job = jobs.create_job(con, "SYNC", body.session_id, 0, body.model_dump())
    con.commit()
    con.close()

    bg.add_task(jobs.run_sync, job["job_id"], body.session_id, sheet_id, body.drive_folder_id, body.full_sync)
    return {"job_id": job["job_id"], "session_id": body.session_id, "status": "QUEUED", "accepted_at": job["created_at"]}


@app.get("/api/v1/sessions/{session_id}/submissions")
def list_submissions(session_id: str, table_id: str | None = None, validation_status: str | None = None):
    con = db.get_db()
    get_session_or_404(con, session_id)
    rows = con.execute(
        "SELECT * FROM submissions WHERE session_id=? ORDER BY submitted_at, created_at",
        (session_id,),
    ).fetchall()
    con.close()

    items = []
    for r in rows:
        if table_id and r["table_id"] != table_id:
            continue
        if validation_status and r["validation_status"] != validation_status:
            continue
        items.append({
            "submission_id": r["submission_id"],
            "table_id": r["table_id"],
            "zone_id": r["zone_id"],
            "submitter": r["submitter"],
            "submitted_at": r["submitted_at"],
            "drive_file_id": r["drive_file_id"],
            "mime_type": r["mime_type"],
            "size": r["size"],
            "photo_accessible": bool(r["photo_accessible"]),
            "photo_url": f"/api/v1/submissions/{r['submission_id']}/photo" if r["drive_file_id"] else None,
            "validation_status": r["validation_status"],
        })
    return {"items": items, "next_cursor": None}


@app.get("/api/v1/submissions/{submission_id}/photo")
def submission_photo(submission_id: str):
    con = db.get_db()
    sub = con.execute("SELECT * FROM submissions WHERE submission_id=?", (submission_id,)).fetchone()
    con.close()

    if not sub or not sub["drive_file_id"]:
        raise HTTPException(status_code=404, detail="사진을 찾을 수 없습니다.")

    data = google_api.download(sub["drive_file_id"])
    return Response(content=data, media_type=sub["mime_type"] or "image/jpeg")


@app.post("/api/v1/sessions/{session_id}/submissions/validate")
def validate_submissions(session_id: str, body: ValidateInput | None = None):
    if body is None:
        body = ValidateInput()

    con = db.get_db()
    get_session_or_404(con, session_id)
    report = jobs.validate_submissions(con, session_id, body.auto_resolve)
    con.commit()
    con.close()
    return report


# ---------------------------------------------------------------- F-04. AI 판독 실행 및 작업 조회

def serialize_job(con, job_id: str) -> dict:
    j = con.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
    if not j:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")

    total = j["total"]
    pct = round(j["completed"] * 100 / total) if total > 0 else 0
    return {
        "job_id": j["job_id"],
        "type": j["type"],
        "session_id": j["session_id"],
        "status": j["status"],
        "progress": {"completed": j["completed"], "total": total, "percentage": pct},
        "failed_items": json.loads(j["failed_items"]),
        "params": json.loads(j["params"]),
        "created_at": j["created_at"],
        "started_at": j["started_at"],
        "finished_at": j["finished_at"],
    }


@app.get("/api/v1/jobs/{job_id}")
def get_job(job_id: str, wait: int = 0):
    timeout = min(max(wait, 0), 30)
    deadline = time.monotonic() + timeout

    while True:
        con = db.get_db()
        try:
            result = serialize_job(con, job_id)
        finally:
            con.close()

        if timeout == 0 or result["status"] in {"SUCCEEDED", "FAILED", "PARTIAL_FAILED"}:
            return result
        if time.monotonic() >= deadline:
            return result
        time.sleep(0.25)


@app.post("/api/v1/sessions/{session_id}/process", status_code=202)
def process_session(session_id: str, bg: BackgroundTasks, body: ProcessInput | None = None):
    if body is None:
        body = ProcessInput()

    con = db.get_db()
    get_session_or_404(con, session_id)

    all_tables = [r["table_id"] for r in con.execute(
        "SELECT table_id FROM tables WHERE session_id=? ORDER BY display_order", (session_id,)
    ).fetchall()]
    latest = jobs.get_latest_results(con, session_id)

    candidates = body.table_ids if body.table_ids else all_tables
    targets = []
    for tid in candidates:
        if body.force or (tid not in latest) or (latest[tid]["status"] == "ERROR"):
            targets.append(tid)

    job = jobs.create_job(con, "AI_ANALYSIS", session_id, len(targets), body.model_dump())
    con.execute("UPDATE sessions SET status='PROCESSING', updated_at=? WHERE session_id=?", (db.now(), session_id))
    con.commit()
    con.close()

    bg.add_task(jobs.run_process, job["job_id"], session_id, targets)
    return {"job_id": job["job_id"], "session_id": session_id, "status": "QUEUED", "target_count": len(targets)}


# ---------------------------------------------------------------- F-05 ~ F-07. 결과 조회 (테이블·구역·전체)

@app.get("/api/v1/sessions/{session_id}/tables")
def list_tables(session_id: str, zone_id: str | None = None, status: str | None = None, q: str | None = None):
    con = db.get_db()
    get_session_or_404(con, session_id)
    rows = get_table_rows(con, session_id)
    con.close()

    filtered = []
    for r in rows:
        if zone_id and r["zone_id"] != zone_id.upper():
            continue
        if status and r["status"] != status.upper():
            continue
        if q and q.upper() not in r["table_id"]:
            continue
        filtered.append(r)

    return {"items": filtered, "next_cursor": None}


@app.get("/api/v1/sessions/{session_id}/tables/{table_id}")
def table_detail(session_id: str, table_id: str):
    con = db.get_db()
    get_session_or_404(con, session_id)
    rows = get_table_rows(con, session_id)

    row = None
    for r in rows:
        if r["table_id"] == table_id:
            row = r
            break
    if not row:
        con.close()
        raise HTTPException(status_code=404, detail="테이블을 찾을 수 없습니다.")

    history = [dict(r) for r in con.execute(
        "SELECT * FROM results WHERE session_id=? AND table_id=? ORDER BY version",
        (session_id, table_id),
    ).fetchall()]

    sub = None
    if row["submission_id"]:
        sub_row = con.execute("SELECT * FROM submissions WHERE submission_id=?", (row["submission_id"],)).fetchone()
        if sub_row:
            sub = dict(sub_row)
    con.close()

    # 가장 마지막 AI 결과와 현재 최종 결과 찾기
    last_ai = None
    for h in history:
        if h["source"] == "AI":
            last_ai = h
    cur = history[-1] if history else None
    ai_json = json.loads(last_ai["ai_json"]) if (last_ai and last_ai["ai_json"]) else {}

    return {
        "table_id": table_id,
        "zone_id": row["zone_id"],
        "table_number": row["table_number"],
        "image": {
            "submission_id": sub["submission_id"],
            "url": row["image_url"],
            "size": sub["size"],
            "mime_type": sub["mime_type"],
            "submitter": sub["submitter"],
            "submitted_at": sub["submitted_at"],
        } if sub else None,
        "ai_result": {
            "status": last_ai["status"],
            "image_quality": ai_json.get("image_quality"),
            "violations": ai_json.get("violations", []),
            "reason": last_ai["reason"],
            "confidence": last_ai["confidence"],
            "model": last_ai["model"],
            "error_code": last_ai["error_code"],
            "version": last_ai["version"],
            "created_at": last_ai["created_at"],
        } if last_ai else None,
        "final_result": {
            "status": cur["status"] if cur else "PENDING",
            "source": cur["source"] if cur else None,
            "reason": cur["reason"] if cur else None,
            "result_version": cur["version"] if cur else 0,
            "updated_by": cur["updated_by"] if cur else None,
            "updated_at": cur["created_at"] if cur else None,
        },
        "history_summary": {
            "version_count": len(history),
            "last_updated_at": cur["created_at"] if cur else None,
            "last_updated_by": cur["updated_by"] if cur else None,
        },
    }


@app.get("/api/v1/sessions/{session_id}/zones")
def get_zones(session_id: str):
    con = db.get_db()
    get_session_or_404(con, session_id)
    rows = get_table_rows(con, session_id)
    con.close()

    zone_ids = sorted(list({r["zone_id"] for r in rows}))
    items = []

    for z in zone_ids:
        z_rows = [r for r in rows if r["zone_id"] == z]
        statuses = [r["status"] for r in z_rows]
        done = sum(1 for s in statuses if s in ("PASS", "FAIL", "REVIEW"))

        # 구역 대표 상태 계산
        if "FAIL" in statuses:
            z_status = "FAIL"
        elif "REVIEW" in statuses or "ERROR" in statuses:
            z_status = "REVIEW"
        elif len(statuses) > 0 and all(s == "PASS" for s in statuses):
            z_status = "PASS"
        else:
            z_status = "PENDING"

        items.append({
            "zone_id": z,
            "name": f"{z} 구역",
            "completed": done,
            "total": len(z_rows),
            "percentage": round(done * 100 / len(z_rows)) if z_rows else 0,
            "status": z_status,
            "summary": count_statuses(z_rows),
            "error_table_ids": [r["table_id"] for r in z_rows if r["status"] == "ERROR"],
        })

    return {"items": items}


@app.get("/api/v1/sessions/{session_id}/overview")
def get_overview(session_id: str):
    con = db.get_db()
    s = get_session_or_404(con, session_id)
    rows = get_table_rows(con, session_id)
    con.close()

    done = sum(1 for r in rows if r["status"] in ("PASS", "FAIL", "REVIEW"))
    return {
        "session_id": session_id,
        "status": s["status"],
        "progress": {
            "completed": done,
            "total": len(rows),
            "percentage": round(done * 100 / len(rows)) if rows else 0,
        },
        "summary": count_statuses(rows),
        "last_updated_at": s["updated_at"],
    }


# ---------------------------------------------------------------- F-08. 재판독 및 관리자 수동 수정

@app.get("/api/v1/sessions/{session_id}/tables/{table_id}/history")
def table_history(session_id: str, table_id: str):
    con = db.get_db()
    get_session_or_404(con, session_id)
    rows = con.execute(
        "SELECT * FROM results WHERE session_id=? AND table_id=? ORDER BY version",
        (session_id, table_id),
    ).fetchall()
    con.close()

    items = []
    for r in rows:
        items.append({
            "version": r["version"],
            "source": r["source"],
            "status": r["status"],
            "reason": r["reason"],
            "confidence": r["confidence"],
            "error_code": r["error_code"],
            "updated_by": r["updated_by"],
            "created_at": r["created_at"],
        })
    return {"items": items}


@app.post("/api/v1/sessions/{session_id}/tables/{table_id}/reprocess", status_code=202)
def reprocess_table(session_id: str, table_id: str, body: ReprocessInput, bg: BackgroundTasks):
    con = db.get_db()
    get_session_or_404(con, session_id)
    job = jobs.create_job(con, "REPROCESS", session_id, 1, {"table_id": table_id, "reason": body.reason})
    con.commit()
    con.close()

    bg.add_task(jobs.run_process, job["job_id"], session_id, [table_id])
    return {"job_id": job["job_id"], "table_id": table_id, "status": "QUEUED"}


@app.post("/api/v1/sessions/{session_id}/tables/{table_id}/reset")
def reset_to_ai(session_id: str, table_id: str):
    con = db.get_db()
    get_session_or_404(con, session_id)

    last_ai = con.execute(
        "SELECT * FROM results WHERE session_id=? AND table_id=? AND source='AI' ORDER BY version DESC LIMIT 1",
        (session_id, table_id),
    ).fetchone()
    if not last_ai:
        con.close()
        raise HTTPException(status_code=404, detail="되돌릴 AI 판독 결과가 없습니다.")

    jobs.save_result(
        con, session_id, table_id,
        source="RESET",
        status=last_ai["status"],
        reason=last_ai["reason"],
        confidence=last_ai["confidence"],
        ai_json=last_ai["ai_json"],
        model=last_ai["model"],
        submission_id=last_ai["submission_id"],
        error_code=last_ai["error_code"],
    )
    jobs.update_session_status(con, session_id)
    con.commit()

    cur = jobs.get_latest_results(con, session_id)[table_id]
    con.close()
    return {
        "table_id": table_id,
        "status": cur["status"],
        "source": cur["source"],
        "reason": cur["reason"],
        "updated_by": cur["updated_by"],
        "updated_at": cur["created_at"],
        "result_version": cur["version"],
    }


@app.patch("/api/v1/sessions/{session_id}/tables/{table_id}/result")
def manual_result(session_id: str, table_id: str, body: ManualResultInput):
    con = db.get_db()
    get_session_or_404(con, session_id)

    cur = jobs.get_latest_results(con, session_id).get(table_id)
    sub_id = cur["submission_id"] if cur else None

    jobs.save_result(
        con, session_id, table_id,
        source="MANUAL",
        status=body.status,
        reason=body.reason,
        submission_id=sub_id,
    )
    jobs.update_session_status(con, session_id)
    con.commit()

    latest = jobs.get_latest_results(con, session_id)[table_id]
    con.close()
    return {
        "table_id": table_id,
        "status": latest["status"],
        "source": latest["source"],
        "reason": latest["reason"],
        "updated_by": latest["updated_by"],
        "updated_at": latest["created_at"],
        "result_version": latest["version"],
    }
