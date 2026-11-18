import json
import re
import ai
import google_api
from db import get_db, new_id, now


# ---------------------------------------------------------------- 1. 시트 데이터 파싱

def find_columns(header: list) -> dict:
    """시트 첫 줄(헤더)에서 각 열의 위치를 찾는다."""
    cols = {}
    for idx, text in enumerate(header):
        h = str(text).strip().lower()
        if "타임스탬프" in h or "timestamp" in h:
            cols["submitted_at"] = idx
        elif "사진" in h or "파일" in h or "photo" in h or "image" in h:
            cols["photo"] = idx
        elif "회차" in h or "session" in h:
            cols["session"] = idx
        elif "구역" in h or "zone" in h:
            cols["zone"] = idx
        elif "테이블" in h or "table" in h:
            cols["table"] = idx
        elif "이름" in h or "제출자" in h or "이메일" in h or "name" in h:
            cols["submitter"] = idx
    return cols


def normalize_table_id(zone_val, table_val):
    """'A-02', 'A2', 또는 구역='A구역'+테이블='2번' 같은 값을 'A-02' 형식으로 통일한다."""
    t = str(table_val or "").strip().upper()
    match = re.search(r"([A-Z])\s*-?\s*(\d{1,2})", t)
    if match:
        return f"{match.group(1)}-{int(match.group(2)):02d}"

    num_match = re.search(r"\d{1,2}", t)
    zone_match = re.search(r"[A-Z]", str(zone_val or "").upper())
    if num_match and zone_match:
        return f"{zone_match.group(0)}-{int(num_match.group(0)):02d}"
    return None


def extract_drive_id(url_text):
    """Google Drive 링크에서 파일 ID만 추출한다."""
    match = re.search(r"(?:[?&]id=|/d/)([\w-]{10,})", str(url_text or ""))
    if match:
        return match.group(1)
    return None


def get_cell(row: list, cols: dict, key: str):
    """행(row)에서 특정 열(key)의 값을 안전하게 꺼낸다."""
    if key not in cols:
        return None
    idx = cols[key]
    if idx >= len(row):
        return None
    return row[idx]


def parse_sheet_rows(values: list, session: dict) -> list:
    """시트 전체 행에서 현재 검사 회차에 해당하는 제출 목록을 추출한다."""
    if not values:
        return []

    cols = find_columns(values[0])
    result = []

    for row in values[1:]:
        submitted_at = str(get_cell(row, cols, "submitted_at") or "").strip() or None
        session_cell = str(get_cell(row, cols, "session") or "").strip()

        # 회차 열이 있으면 회차 ID나 날짜가 일치하는 행만 가져온다
        if session_cell:
            if session["session_id"] not in session_cell and session["inspection_date"] not in session_cell:
                continue

        table_id = normalize_table_id(get_cell(row, cols, "zone"), get_cell(row, cols, "table"))
        file_id = extract_drive_id(get_cell(row, cols, "photo"))
        submitter = str(get_cell(row, cols, "submitter") or "").strip() or None
        zone_id = table_id[0] if table_id else None

        row_key = f"{submitted_at}|{submitter}|{file_id}|{table_id}"
        result.append({
            "row_key": row_key,
            "table_id": table_id,
            "zone_id": zone_id,
            "submitter": submitter,
            "submitted_at": submitted_at,
            "drive_file_id": file_id,
        })
    return result


# ---------------------------------------------------------------- 2. 결과 저장 및 상태 계산

def get_latest_results(con, session_id: str) -> dict:
    """테이블마다 가장 최신(version이 가장 큰) 결과를 딕셔너리로 반환한다."""
    rows = con.execute(
        "SELECT * FROM results WHERE session_id=? ORDER BY version ASC",
        (session_id,),
    ).fetchall()
    latest = {}
    for r in rows:
        latest[r["table_id"]] = dict(r)  # 순서대로 덮어쓰면 마지막이 최신 버전이 됨
    return latest


def save_result(con, session_id: str, table_id: str, source: str, status: str, reason: str,
                updated_by: str = "admin", confidence=None, ai_json=None,
                model=None, submission_id=None, error_code=None) -> int:
    """새로운 버전의 결과를 results 테이블에 추가한다."""
    row = con.execute(
        "SELECT COALESCE(MAX(version), 0) + 1 FROM results WHERE session_id=? AND table_id=?",
        (session_id, table_id),
    ).fetchone()
    next_version = row[0]

    con.execute(
        """INSERT INTO results (
            session_id, table_id, version, source, status, reason,
            confidence, ai_json, model, submission_id, error_code, updated_by, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (session_id, table_id, next_version, source, status, reason,
         confidence, ai_json, model, submission_id, error_code, updated_by, now()),
    )
    return next_version


def update_session_status(con, session_id: str):
    """모든 테이블의 결과가 나왔으면 회차 상태를 COMPLETED로 바꾼다."""
    session = con.execute("SELECT status FROM sessions WHERE session_id=?", (session_id,)).fetchone()
    if not session or session["status"] == "CLOSED":
        return

    tables = con.execute("SELECT table_id FROM tables WHERE session_id=?", (session_id,)).fetchall()
    latest = get_latest_results(con, session_id)

    all_done = True
    for t in tables:
        tid = t["table_id"]
        if tid not in latest or latest[tid]["status"] not in ("PASS", "FAIL", "REVIEW"):
            all_done = False
            break

    if all_done and len(tables) > 0:
        con.execute("UPDATE sessions SET status='COMPLETED', updated_at=? WHERE session_id=?", (now(), session_id))


# ---------------------------------------------------------------- 3. 제출 검증 (누락·중복 확인)

def validate_submissions(con, session_id: str, auto_resolve: bool = False) -> dict:
    """16개 테이블의 사진이 빠짐없이, 중복 없이 제출되었는지 검사한다."""
    table_rows = con.execute(
        "SELECT table_id FROM tables WHERE session_id=? ORDER BY display_order",
        (session_id,),
    ).fetchall()
    table_ids = [r["table_id"] for r in table_rows]

    subs = con.execute(
        "SELECT * FROM submissions WHERE session_id=? ORDER BY submitted_at, created_at",
        (session_id,),
    ).fetchall()

    status_map = {}
    by_table = {}

    for s in subs:
        sid = s["submission_id"]
        tid = s["table_id"]
        if not s["drive_file_id"]:
            status_map[sid] = "NO_PHOTO"
        elif tid not in table_ids:
            status_map[sid] = "UNMAPPED"
        elif not s["photo_accessible"]:
            status_map[sid] = "PHOTO_NOT_ACCESSIBLE"
        else:
            if tid not in by_table:
                by_table[tid] = []
            by_table[tid].append(sid)

    duplicates = []
    for tid, sid_list in by_table.items():
        if len(sid_list) == 1:
            status_map[sid_list[0]] = "VALID"
        elif auto_resolve:
            # 자동 해결 옵션이 켜져 있으면 가장 마지막 제출만 VALID로 인정
            for old_id in sid_list[:-1]:
                status_map[old_id] = "SUPERSEDED"
            status_map[sid_list[-1]] = "VALID"
        else:
            for dup_id in sid_list:
                status_map[dup_id] = "DUPLICATE"
            duplicates.append({"table_id": tid, "submission_ids": sid_list})

    for sid, st in status_map.items():
        con.execute("UPDATE submissions SET validation_status=? WHERE submission_id=?", (st, sid))

    missing = [tid for tid in table_ids if tid not in by_table]
    unmapped = [sid for sid, st in status_map.items() if st == "UNMAPPED"]

    warnings = []
    for d in duplicates:
        warnings.append(f"{d['table_id']} 테이블에 중복 제출이 있습니다.")
    for tid in missing:
        warnings.append(f"{tid} 테이블의 제출이 없습니다.")

    report = {
        "valid": (len(duplicates) == 0 and len(missing) == 0),
        "expected_count": len(table_ids),
        "received_count": len(by_table),
        "duplicates": duplicates,
        "missing_table_ids": missing,
        "unmapped_submission_ids": unmapped,
        "warnings": warnings,
    }

    con.execute(
        "UPDATE sessions SET validation_json=?, validated_at=?, updated_at=? WHERE session_id=?",
        (json.dumps(report, ensure_ascii=False), now(), now(), session_id),
    )
    return report


# ---------------------------------------------------------------- 4. 비동기 작업 (동기화 & AI 판독)

def create_job(con, job_type: str, session_id: str, total: int, params: dict) -> dict:
    """새 작업(Job)을 DB에 등록한다."""
    job_id = new_id(f"job_{job_type.lower()}")
    created = now()
    con.execute(
        "INSERT INTO jobs (job_id, type, session_id, status, total, params, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (job_id, job_type, session_id, "QUEUED", total, json.dumps(params, ensure_ascii=False), created),
    )
    return {"job_id": job_id, "created_at": created}


def run_sync(job_id: str, session_id: str, sheet_id: str, drive_folder_id, full_sync: bool):
    """백그라운드에서 Google Sheets의 제출 내역을 읽어 DB에 저장한다."""
    con = get_db()
    con.execute("UPDATE jobs SET status='RUNNING', started_at=? WHERE job_id=?", (now(), job_id))
    con.commit()

    try:
        session = dict(con.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone())
        values = google_api.read_sheet(sheet_id)
        rows = parse_sheet_rows(values, session)

        con.execute("UPDATE jobs SET total=? WHERE job_id=?", (len(rows), job_id))
        if full_sync:
            con.execute("DELETE FROM submissions WHERE session_id=?", (session_id,))
        con.commit()

        existing = con.execute("SELECT row_key FROM submissions WHERE session_id=?", (session_id,)).fetchall()
        seen_keys = {r["row_key"] for r in existing}

        completed = 0
        for r in rows:
            if r["row_key"] not in seen_keys:
                meta = google_api.file_meta(r["drive_file_id"]) if r["drive_file_id"] else None
                mime = meta.get("mimeType") if meta else None
                size = int(meta["size"]) if (meta and meta.get("size")) else None
                accessible = 1 if (mime and mime.startswith("image/")) else 0

                con.execute(
                    """INSERT OR IGNORE INTO submissions (
                        submission_id, session_id, row_key, table_id, zone_id,
                        submitter, submitted_at, drive_file_id, mime_type, size,
                        photo_accessible, validation_status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (new_id("sub"), session_id, r["row_key"], r["table_id"], r["zone_id"],
                     r["submitter"], r["submitted_at"], r["drive_file_id"], mime, size,
                     accessible, "PENDING", now()),
                )
                seen_keys.add(r["row_key"])

            completed += 1
            con.execute("UPDATE jobs SET completed=? WHERE job_id=?", (completed, job_id))
            con.commit()

        con.execute(
            "UPDATE sessions SET sheet_id=?, drive_folder_id=?, last_synced_at=?, status='COLLECTING', updated_at=? WHERE session_id=?",
            (sheet_id, drive_folder_id, now(), now(), session_id),
        )
        validate_submissions(con, session_id)
        con.execute("UPDATE jobs SET status='SUCCEEDED', finished_at=? WHERE job_id=?", (now(), job_id))
        con.commit()
    except Exception as e:
        failed = json.dumps([{"code": "SYNC_ERROR", "message": str(e)}], ensure_ascii=False)
        con.execute("UPDATE jobs SET status='FAILED', failed_items=?, finished_at=? WHERE job_id=?", (failed, now(), job_id))
        con.commit()
    finally:
        con.close()


def run_process(job_id: str, session_id: str, table_ids: list):
    """백그라운드에서 각 테이블의 사진을 다운로드해 Gemini AI로 판독한다."""
    con = get_db()
    con.execute("UPDATE jobs SET status='RUNNING', started_at=? WHERE job_id=?", (now(), job_id))
    con.commit()

    failed = []
    completed = 0

    for tid in table_ids:
        sub = con.execute(
            "SELECT * FROM submissions WHERE session_id=? AND table_id=? AND validation_status='VALID'",
            (session_id, tid),
        ).fetchone()

        if not sub:
            failed.append({"table_id": tid, "code": "TABLE_MISSING", "message": "검증을 통과한 사진이 없습니다."})
            completed += 1
            con.execute("UPDATE jobs SET completed=? WHERE job_id=?", (completed, job_id))
            con.commit()
            continue

        try:
            image_bytes = google_api.download(sub["drive_file_id"])
            ai_res = ai.analyze(image_bytes, sub["mime_type"] or "image/jpeg", tid)
            final_status = ai.judge(ai_res)

            save_result(
                con, session_id, tid,
                source="AI",
                status=final_status,
                reason=ai_res.reason,
                updated_by="AI",
                confidence=ai_res.confidence,
                ai_json=ai_res.model_dump_json(),
                model=ai.MODEL,
                submission_id=sub["submission_id"],
            )
        except Exception as e:
            save_result(
                con, session_id, tid,
                source="AI",
                status="ERROR",
                reason=str(e),
                updated_by="AI",
                model=ai.MODEL,
                submission_id=sub["submission_id"],
                error_code="AI_ERROR",
            )
            failed.append({"table_id": tid, "code": "AI_ERROR", "message": str(e)})

        completed += 1
        con.execute("UPDATE jobs SET completed=? WHERE job_id=?", (completed, job_id))
        con.commit()

    update_session_status(con, session_id)

    if len(failed) == 0:
        job_status = "SUCCEEDED"
    elif len(failed) >= len(table_ids):
        job_status = "FAILED"
    else:
        job_status = "PARTIAL_FAILED"

    con.execute(
        "UPDATE jobs SET status=?, failed_items=?, finished_at=? WHERE job_id=?",
        (job_status, json.dumps(failed, ensure_ascii=False), now(), job_id),
    )
    con.commit()
    con.close()
