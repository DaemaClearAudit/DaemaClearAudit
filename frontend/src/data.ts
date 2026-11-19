import { AREAS, STATUS_INFO, STORAGE_KEY } from "./constants/inspection.ts";
import type { AppData, Area, Session, Status, Table } from "./types/index.ts";

export { AREAS as areas, STATUS_INFO as statusInfo, STORAGE_KEY } from "./constants/inspection.ts";
export type { AppData, Area, Session, Status, Table } from "./types/index.ts";

const seeds: readonly (readonly [Status, string, number | null])[] = [
  ["FAIL", "테이블 위에 휴지가 보입니다.", 0.91],
  ["PASS", "테이블 상판이 깨끗합니다.", 0.98],
  ["REVIEW", "사진이 흐려 테이블 상태를 확인하기 어렵습니다.", 0.58],
  ["PASS", "청소 불량 항목이 발견되지 않았습니다.", 0.96],
  ["PASS", "테이블 상판이 깨끗합니다.", 0.95],
  ["FAIL", "테이블 위에 음료 캔이 보입니다.", 0.93],
  ["PASS", "청소 불량 항목이 발견되지 않았습니다.", 0.97],
  ["PENDING", "", null],
  ["PASS", "테이블 상판이 깨끗합니다.", 0.99],
  ["PASS", "청소 불량 항목이 발견되지 않았습니다.", 0.94],
  ["ERROR", "사진을 판독하지 못했습니다. 재판독이 필요합니다.", null],
  ["PENDING", "", null],
  ["PASS", "테이블 상판이 깨끗합니다.", 0.97],
  ["REVIEW", "테이블 일부가 가려져 확인이 필요합니다.", 0.62],
  ["PENDING", "", null],
  ["PENDING", "", null],
];

export function makeSession(name: string, demo = false): Session {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    name,
    date: new Date().toISOString(),
    closed: false,
    tables: AREAS.flatMap((area, a) =>
      Array.from({ length: 4 }, (_, i): Table => {
        const [status, reason, confidence] = demo
          ? seeds[a * 4 + i]
          : (["PENDING", "", null] as const);
        return {
          id: `${area}-0${i + 1}`,
          area,
          status,
          reason,
          confidence,
          revised: false,
          history: status === "PENDING" ? [] : [{ text: "예시 판독 결과", time: "11:18" }],
        };
      }),
    ),
  };
}

export function loadData(): AppData {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const data: unknown = raw ? JSON.parse(raw) : null;
    if (
      data &&
      typeof data === "object" &&
      "sessions" in data &&
      Array.isArray(data.sessions) &&
      data.sessions.length
    )
      return data as AppData;
  } catch {}
  return { sessions: [makeSession("오전 검사", true)] };
}

export function saveData(data: AppData): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

export function counts(tables: readonly Table[]): Record<Status, number> {
  const result: Record<Status, number> = {
    PASS: 0,
    FAIL: 0,
    REVIEW: 0,
    ERROR: 0,
    PENDING: 0,
  };
  for (const table of tables) result[table.status]++;
  return result;
}

export function areaStatus(tables: readonly Table[]): Status {
  if (tables.some((table) => table.status === "FAIL")) return "FAIL";
  if (tables.some((table) => table.status === "REVIEW" || table.status === "ERROR"))
    return "REVIEW";
  if (tables.length === 4 && tables.every((table) => table.status === "PASS")) return "PASS";
  return "PENDING";
}
