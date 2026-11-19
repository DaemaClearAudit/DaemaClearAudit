import { apiUrl, request } from "./client";
import type { AppData, Area, HistoryEntry, Session, Status, Table } from "../types";

interface SessionSummaryResponse {
  session_id: string;
  inspection_date: string;
  status: string;
  expected_table_count: number;
  submitted_count: number;
  completed_count: number;
  last_updated_at: string | null;
}

interface SessionListResponse {
  items: SessionSummaryResponse[];
  next_cursor: string | null;
}

interface BackendTableRow {
  table_id: string;
  zone_id: string;
  table_number: number;
  status: string;
  source: string | null;
  confidence: number | null;
  image_url: string | null;
  submission_id: string | null;
  submitted_at: string | null;
  result_version: number;
}

interface TableListResponse {
  items: BackendTableRow[];
  next_cursor: string | null;
}

interface TableHistoryResponse {
  items: Array<{
    version: number;
    source: string;
    status: string;
    reason: string | null;
    confidence: number | null;
    error_code: string | null;
    updated_by: string | null;
    created_at: string;
  }>;
}

interface TableDetailResponse {
  table_id: string;
  zone_id: string;
  image: {
    submission_id: string;
    url: string | null;
    size: number | null;
    mime_type: string | null;
    submitter: string | null;
    submitted_at: string | null;
  } | null;
  ai_result: {
    status: string;
    reason: string | null;
    confidence: number | null;
  } | null;
  final_result: {
    status: string;
    source: string | null;
    reason: string | null;
    result_version: number;
  };
}

interface JobResponse {
  job_id: string;
  status: string;
  progress: { completed: number; total: number; percentage: number };
  failed_items: Array<{ code: string; message: string; table_id?: string }>;
}

interface SessionCreateResponse extends SessionSummaryResponse {
  session_id: string;
}

function toStatus(value: string): Status {
  const normalized = value.toUpperCase();
  if (["PASS", "FAIL", "REVIEW", "ERROR", "PENDING"].includes(normalized)) {
    return normalized as Status;
  }
  return "PENDING";
}

function toArea(value: string): Area {
  const normalized = value.toUpperCase();
  return ["A", "B", "C", "D"].includes(normalized) ? (normalized as Area) : "A";
}

function historyText(item: TableHistoryResponse["items"][number]): string {
  if (item.reason) return item.reason;
  if (item.updated_by) return `${item.updated_by} 판정`;
  return `${item.source} 판정`;
}

function historyTime(value: string): string {
  return value.includes("T") ? value.slice(11, 16) : value;
}

async function getTableData(sessionId: string, row: BackendTableRow): Promise<Table> {
  const [detail, history] = await Promise.all([
    request<TableDetailResponse>(`/sessions/${sessionId}/tables/${row.table_id}`).catch(() => null),
    request<TableHistoryResponse>(`/sessions/${sessionId}/tables/${row.table_id}/history`).catch(
      () => ({ items: [] }),
    ),
  ]);
  const finalResult = detail?.final_result;
  const aiResult = detail?.ai_result;
  const source = finalResult?.source ?? row.source;

  const mappedHistory: HistoryEntry[] = history.items.map((item) => ({
    text: historyText(item),
    time: historyTime(item.created_at),
  }));

  return {
    id: row.table_id,
    area: toArea(row.zone_id),
    status: toStatus(finalResult?.status ?? row.status),
    reason: finalResult?.reason ?? aiResult?.reason ?? "",
    confidence: aiResult?.confidence ?? row.confidence,
    revised: source === "MANUAL" || source === "RESET",
    history: mappedHistory,
    source,
    imageUrl: apiUrl(detail?.image?.url ?? row.image_url ?? ""),
    submissionId: detail?.image?.submission_id ?? row.submission_id,
    submittedAt: detail?.image?.submitted_at ?? row.submitted_at,
    resultVersion: finalResult?.result_version ?? row.result_version,
  };
}

async function getSessionData(summary: SessionSummaryResponse, index: number): Promise<Session> {
  const tables = await request<TableListResponse>(`/sessions/${summary.session_id}/tables`);
  const mappedTables = await Promise.all(
    tables.items.map((table) => getTableData(summary.session_id, table)),
  );

  return {
    id: summary.session_id,
    name: `${index + 1}회차`,
    date: summary.inspection_date,
    closed: summary.status === "CLOSED",
    tables: mappedTables,
  };
}

export async function fetchInspectionData(): Promise<AppData> {
  const response = await request<SessionListResponse>("/sessions");
  let items = response.items;

  if (!items.length) {
    const today = new Date().toISOString().slice(0, 10);
    const created = await request<SessionCreateResponse>("/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        inspection_date: today,
        started_at: new Date().toISOString(),
        expected_table_count: 16,
        zone_count: 4,
      }),
    });
    items = [created];
  }

  return {
    sessions: await Promise.all(items.map((item, index) => getSessionData(item, index))),
  };
}

export function createApiSession(inspectionDate: string) {
  return request<SessionCreateResponse>("/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      inspection_date: inspectionDate,
      started_at: new Date().toISOString(),
      expected_table_count: 16,
      zone_count: 4,
    }),
  });
}

export function closeApiSession(sessionId: string) {
  return request<SessionSummaryResponse>(`/sessions/${sessionId}/close`, { method: "POST" });
}

export function setManualResult(
  sessionId: string,
  tableId: string,
  status: "PASS" | "FAIL" | "REVIEW",
  reason: string,
) {
  return request(`/sessions/${sessionId}/tables/${tableId}/result`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status, reason: reason || "관리자가 수동으로 판정을 수정했습니다." }),
  });
}

export function reprocessApiTable(sessionId: string, tableId: string, reason: string) {
  return request<{ job_id: string; table_id: string; status: string }>(
    `/sessions/${sessionId}/tables/${tableId}/reprocess`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason: reason || "관리자가 재판독을 요청했습니다.", force: true }),
    },
  );
}

export function processApiTable(sessionId: string, tableId: string) {
  return request<{ job_id: string; session_id: string; status: string }>(
    `/sessions/${sessionId}/process`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ table_ids: [tableId], force: true }),
    },
  );
}

export function getApiJob(jobId: string, waitSeconds = 0) {
  const query = waitSeconds > 0 ? `?wait=${waitSeconds}` : "";
  return request<JobResponse>(`/jobs/${jobId}${query}`);
}

export async function waitForApiJob(jobId: string): Promise<JobResponse> {
  for (let attempt = 0; attempt < 4; attempt += 1) {
    const job = await getApiJob(jobId, 25);
    if (["SUCCEEDED", "FAILED", "PARTIAL_FAILED"].includes(job.status)) return job;
  }
  throw new Error("판독 작업이 오래 걸리고 있습니다. 잠시 후 새로고침해 주세요.");
}
