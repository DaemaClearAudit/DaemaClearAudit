import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
  closeApiSession,
  createApiSession,
  fetchInspectionData,
  processApiTable,
  reprocessApiTable,
  setManualResult,
  waitForApiJob,
} from "../api/inspection.api";
import { counts, loadData, makeSession, saveData } from "../data";
import { STATUS_INFO } from "../constants/inspection";
import type { AppData, Filter, InspectionAction, Table, View } from "../types";

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "API 요청에 실패했습니다.";
}

export function useInspection() {
  const [data, setData] = useState<AppData>(loadData);
  const [sessionId, setSessionId] = useState(data.sessions[0].id);
  const [view, setView] = useState<View>("dashboard");
  const [selectedArea, setSelectedArea] = useState("전체");
  const [filter, setFilter] = useState<Filter>("전체");
  const [selectedId, setSelectedId] = useState("A-01");
  const [search, setSearch] = useState("");
  const [detailOpen, setDetailOpen] = useState(false);
  const [overlay, setOverlay] = useState(false);
  const [message, setMessage] = useState("");
  const [reason, setReason] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [sessionName, setSessionName] = useState("");
  const [apiConnected, setApiConnected] = useState(false);

  async function refreshFromApi() {
    const next = await fetchInspectionData();
    setData(next);
    saveData(next);
    setSessionId((current) =>
      next.sessions.some((item) => item.id === current) ? current : next.sessions[0].id,
    );
    setApiConnected(true);
    return next;
  }

  useEffect(() => {
    refreshFromApi().catch((error) => {
      setApiConnected(false);
      setMessage(`백엔드 연결 실패: ${errorMessage(error)} 시연용 데이터를 표시합니다.`);
    });
  }, []);

  const session = data.sessions.find((item) => item.id === sessionId) ?? data.sessions[0];
  const sessionIndex = Math.max(
    data.sessions.findIndex((item) => item.id === session.id),
    0,
  );
  const sessionLabel = `${sessionIndex + 1}회차`;
  const tables = session.tables;
  const c = counts(tables);
  const queue = tables.filter((table) => table.status === "REVIEW" || table.status === "ERROR");
  const selected = tables.find((table) => table.id === selectedId) ?? tables[0];
  const reviewTable = queue.find((table) => table.id === selectedId) ?? queue[0];
  const visible = tables.filter(
    (table) =>
      (selectedArea === "전체" || table.area === selectedArea) &&
      (filter === "전체" || (filter === "수정됨" ? table.revised : table.status === filter)) &&
      table.id.toLowerCase().includes(search.toLowerCase()),
  );

  function commit(next: AppData) {
    setData(next);
    saveData(next);
  }

  async function updateSelected(table: Table, kind: InspectionAction) {
    if (session.closed || (table.status === "PENDING" && kind !== "submit")) return;

    if (apiConnected) {
      try {
        if (kind === "PASS" || kind === "FAIL") {
          await setManualResult(session.id, table.id, kind, reason);
          await refreshFromApi();
          setMessage(`${table.id} 판정을 ${STATUS_INFO[kind][0]}(으)로 수정했습니다.`);
        } else {
          const job =
            kind === "reprocess"
              ? await reprocessApiTable(session.id, table.id, reason)
              : await processApiTable(session.id, table.id);
          setMessage(`${table.id} 판독 작업을 시작했습니다.`);
          const result = await waitForApiJob(job.job_id);
          await refreshFromApi();
          setMessage(
            result.status === "SUCCEEDED"
              ? `${table.id} 판독이 완료되었습니다.`
              : `${table.id} 판독이 완료되지 않았습니다. 결과를 확인해 주세요.`,
          );
        }
        setReason("");
      } catch (error) {
        setMessage(errorMessage(error));
      }
      return;
    }

    const next = structuredClone(data);
    const target = next.sessions
      .find((item) => item.id === session.id)!
      .tables.find((item) => item.id === table.id)!;
    let text: string;
    if (kind === "submit") {
      target.status = "PASS";
      target.reason = "시연용 사진에서 청소 불량 항목이 발견되지 않았습니다.";
      target.confidence = 0.96;
      text = `${table.id} 예시 사진을 제출했습니다.`;
    } else if (kind === "reprocess") {
      target.status = "REVIEW";
      target.reason = "시연용 재판독 요청이 접수되었습니다. 관리자 확인이 필요합니다.";
      target.confidence = null;
      text = `${table.id} 재판독을 요청했습니다. (시연)`;
    } else {
      target.status = kind;
      target.revised = true;
      if (reason.trim()) target.reason = reason.trim();
      text = `${table.id} 판정을 ${STATUS_INFO[kind][0]}(으)로 수정했습니다.`;
    }
    target.history.push({
      text,
      time: new Intl.DateTimeFormat("ko-KR", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      }).format(new Date()),
    });
    commit(next);
    setMessage(text);
    setReason("");
  }

  function changeSession(id: string) {
    setSessionId(id);
    setSelectedId("A-01");
    setSelectedArea("전체");
    setFilter("전체");
    setMessage("");
    setReason("");
  }

  async function createSession(event: FormEvent) {
    event.preventDefault();
    if (!sessionName.trim()) return;

    if (apiConnected) {
      try {
        const created = await createApiSession(new Date().toISOString().slice(0, 10));
        await refreshFromApi();
        changeSession(created.session_id);
        setView("dashboard");
        setDialogOpen(false);
        setSessionName("");
        setMessage("새 검사 회차를 만들었습니다.");
      } catch (error) {
        setMessage(errorMessage(error));
      }
      return;
    }

    const created = makeSession(sessionName.trim());
    commit({ sessions: [...data.sessions, created] });
    changeSession(created.id);
    setView("dashboard");
    setDialogOpen(false);
    setSessionName("");
    setMessage("새 검사 회차를 만들었습니다.");
  }

  async function toggleSession() {
    if (!session.closed && tables.some((table) => table.status === "PENDING")) {
      setMessage("미제출 테이블이 있어 회차를 종료할 수 없습니다.");
      return;
    }

    if (apiConnected) {
      if (session.closed) {
        setMessage("백엔드 회차는 종료 후 다시 열 수 없습니다.");
        return;
      }
      try {
        await closeApiSession(session.id);
        await refreshFromApi();
        setMessage("검사 회차를 종료했습니다.");
      } catch (error) {
        setMessage(errorMessage(error));
      }
      return;
    }

    const next = structuredClone(data);
    const target = next.sessions.find((item) => item.id === session.id)!;
    target.closed = !target.closed;
    commit(next);
    setMessage(target.closed ? "검사 회차를 종료했습니다." : "검사 회차를 다시 열었습니다.");
  }

  function navigate(next: View) {
    setView(next);
    if (next === "manage") setDetailOpen(true);
    setMessage("");
    setReason("");
  }

  function selectTable(id: string) {
    setSelectedId(id);
    setDetailOpen(true);
    setOverlay(false);
    setReason("");
  }

  return {
    data,
    view,
    selectedArea,
    setSelectedArea,
    filter,
    setFilter,
    selectedId,
    setSelectedId,
    search,
    setSearch,
    detailOpen,
    setDetailOpen,
    overlay,
    setOverlay,
    message,
    setMessage,
    reason,
    setReason,
    dialogOpen,
    setDialogOpen,
    sessionName,
    setSessionName,
    session,
    sessionLabel,
    tables,
    c,
    queue,
    selected,
    reviewTable,
    visible,
    updateSelected,
    changeSession,
    createSession,
    toggleSession,
    navigate,
    selectTable,
  };
}
