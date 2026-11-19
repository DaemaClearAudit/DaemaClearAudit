import type { Area, Status } from "../types/index.ts";

export const STORAGE_KEY = "classclean-demo-v1";
export const AREAS: readonly Area[] = ["A", "B", "C", "D"];
export const STATUS_INFO: Record<Status, readonly [string, string]> = {
  PASS: ["정상", "pass"],
  FAIL: ["이상", "fail"],
  REVIEW: ["검토 필요", "review"],
  ERROR: ["오류", "error"],
  PENDING: ["미제출", "pending"],
};
