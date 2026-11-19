import { PanelRightOpen, Search } from "lucide-react";
import * as styles from "../../styles";
import { AREAS, STATUS_INFO } from "../../constants/inspection";
import type { Filter, InspectionAction, Status, Table } from "../../types";
import { Badge, Photo } from "../../components/inspection/InspectionVisuals";
import { InspectionDetail } from "../../components/inspection/InspectionDetail";

interface ManagePageProps {
  tables: Table[];
  visibleTables: Table[];
  counts: Record<Status, number>;
  selectedArea: string;
  filter: Filter;
  selectedId: string;
  search: string;
  detailOpen: boolean;
  closed: boolean;
  reason: string;
  overlay: boolean;
  sessionDate: string;
  onAreaChange: (area: string) => void;
  onFilterChange: (filter: Filter) => void;
  onSelectTable: (id: string) => void;
  onSearchChange: (search: string) => void;
  onDetailToggle: (open: boolean) => void;
  onReasonChange: (reason: string) => void;
  onUpdate: (table: Table, action: InspectionAction) => void;
  onOverlayChange: (overlay: boolean) => void;
}

export function ManagePage({
  tables,
  visibleTables,
  counts,
  selectedArea,
  filter,
  selectedId,
  search,
  detailOpen,
  closed,
  reason,
  overlay,
  sessionDate,
  onAreaChange,
  onFilterChange,
  onSelectTable,
  onSearchChange,
  onDetailToggle,
  onReasonChange,
  onUpdate,
  onOverlayChange,
}: ManagePageProps) {
  const selected = tables.find((table) => table.id === selectedId) ?? tables[0];
  const filters: [Filter, number][] = [
    ["전체", tables.length],
    ["FAIL", counts.FAIL],
    ["REVIEW", counts.REVIEW],
    ["ERROR", counts.ERROR],
    ["PASS", counts.PASS],
    ["PENDING", counts.PENDING],
    ["수정됨", tables.filter((table) => table.revised).length],
  ];

  return (
    <div css={styles.manageLayout}>
      <div css={styles.managePanel}>
        <div css={styles.manageHeader}>
          <div>
            <h2>테이블 판독 결과</h2>
            <p>구역과 상태별로 점검 결과를 살펴보세요.</p>
          </div>
          <label css={styles.searchField}>
            <Search aria-hidden="true" size={15} css={styles.inputIcon} />
            <input
              placeholder="테이블 번호 검색"
              aria-label="테이블 번호 검색"
              value={search}
              onChange={(event) => onSearchChange(event.target.value)}
            />
          </label>
        </div>
        <div css={styles.areaTabs}>
          {["전체", ...AREAS].map((area) => (
            <button
              key={area}
              css={selectedArea === area ? styles.areaTabActive : null}
              onClick={() => onAreaChange(area)}
            >
              {area === "전체" ? "전체 구역" : `${area} 구역`}
            </button>
          ))}
        </div>
        <div css={styles.filterTabs}>
          {filters.map(([key, count]) => (
            <button
              key={key}
              css={[styles.filterButton, filter === key ? styles.filterButtonActive : null]}
              onClick={() => onFilterChange(key)}
            >
              {key === "전체" || key === "수정됨" ? key : STATUS_INFO[key][0]} <span>{count}</span>
            </button>
          ))}
        </div>
        <div css={styles.tableGrid}>
          {visibleTables.length ? (
            visibleTables.map((table) => (
              <button
                key={table.id}
                css={[
                  styles.tableCard,
                  selectedId === table.id && detailOpen ? styles.tableCardActive : null,
                ]}
                onClick={() => onSelectTable(table.id)}
              >
                <Photo table={table} />
                <div css={styles.tableCardBody}>
                  <div>
                    <strong>{table.id}</strong>
                    <Badge status={table.status} />
                  </div>
                  <p>
                    {table.confidence == null
                      ? "판독 정보 없음"
                      : `신뢰도 ${Math.round(table.confidence * 100)}%`}
                  </p>
                </div>
              </button>
            ))
          ) : (
            <div css={styles.emptyState}>조건에 맞는 테이블이 없습니다.</div>
          )}
        </div>
        <p css={styles.tableCount}>{visibleTables.length}개 테이블 표시</p>
      </div>
      {detailOpen ? (
        <InspectionDetail
          table={selected}
          closed={closed}
          reason={reason}
          onReasonChange={onReasonChange}
          onUpdate={onUpdate}
          overlay={overlay}
          onOverlayChange={onOverlayChange}
          sessionDate={sessionDate}
          onClose={() => onDetailToggle(false)}
        />
      ) : (
        <button css={styles.openDetailsButton} onClick={() => onDetailToggle(true)}>
          <PanelRightOpen aria-hidden="true" size={16} css={styles.inputIcon} /> 상세 열기
        </button>
      )}
    </div>
  );
}
