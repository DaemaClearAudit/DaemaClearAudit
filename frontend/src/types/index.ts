export type Area = "A" | "B" | "C" | "D";
export type Status = "PASS" | "FAIL" | "REVIEW" | "ERROR" | "PENDING";
export type View = "dashboard" | "manage" | "review";
export type Filter = "전체" | "수정됨" | Status;
export type InspectionAction = "PASS" | "FAIL" | "reprocess" | "submit";

export interface HistoryEntry {
  text: string;
  time: string;
}

export interface Table {
  id: string;
  area: Area;
  status: Status;
  reason: string;
  confidence: number | null;
  revised: boolean;
  history: HistoryEntry[];
  source?: string | null;
  imageUrl?: string | null;
  submissionId?: string | null;
  submittedAt?: string | null;
  resultVersion?: number;
}

export interface Session {
  id: string;
  name: string;
  date: string;
  closed: boolean;
  tables: Table[];
}

export interface AppData {
  sessions: Session[];
}
