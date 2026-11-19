import type { View } from "../types";
import type { LucideIcon } from "lucide-react";
import { CircleAlert, LayoutDashboard, ListChecks } from "lucide-react";

export const inspectionRoutes: readonly {
  id: View;
  label: string;
  icon: LucideIcon;
}[] = [
  { id: "dashboard", label: "전체 현황", icon: LayoutDashboard },
  { id: "manage", label: "판독 관리", icon: ListChecks },
  { id: "review", label: "검토 대기", icon: CircleAlert },
];
