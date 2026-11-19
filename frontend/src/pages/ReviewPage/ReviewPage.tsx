import type { SerializedStyles } from "@emotion/react";
import { Check } from "lucide-react";
import * as styles from "../../styles";
import { AREAS, STATUS_INFO } from "../../constants/inspection";
import type { InspectionAction, Status, Table } from "../../types";
import { Badge, Photo } from "../../components/inspection/InspectionVisuals";
import { InspectionActions, PhotoTabs } from "../../components/inspection/InspectionDetail";
import { formatDate } from "../../utils/formatDate";

interface ReviewPageProps {
  tables: Table[];
  queue: Table[];
  reviewTable: Table | undefined;
  closed: boolean;
  reason: string;
  overlay: boolean;
  sessionDate: string;
  onSelectTable: (id: string) => void;
  onOverlayChange: (overlay: boolean) => void;
  onReasonChange: (reason: string) => void;
  onUpdate: (table: Table, action: InspectionAction) => void;
  onOpenManage: () => void;
}

const statusStyles: Record<Status, SerializedStyles> = {
  PASS: styles.passSwatch,
  FAIL: styles.failSwatch,
  REVIEW: styles.reviewSwatch,
  ERROR: styles.reviewSwatch,
  PENDING: styles.pendingSwatch,
};

export function ReviewPage({
  tables,
  queue,
  reviewTable,
  closed,
  reason,
  overlay,
  sessionDate,
  onSelectTable,
  onOverlayChange,
  onReasonChange,
  onUpdate,
  onOpenManage,
}: ReviewPageProps) {
  if (!reviewTable) {
    return (
      <div css={styles.reviewEmpty}>
        <div>
          <Check aria-hidden="true" size={24} />
        </div>
        <h2>검토할 항목이 없습니다</h2>
        <p>모든 검토 대기 항목을 확인했어요.</p>
        <button css={styles.primaryButton} onClick={onOpenManage}>
          판독 관리로 이동
        </button>
      </div>
    );
  }

  return (
    <>
      <div css={styles.sectionHeading}>
        <div>
          <h2>검토가 필요한 테이블</h2>
          <p>판독이 불확실하거나 오류가 발생한 항목을 확인하세요.</p>
        </div>
        <span css={styles.queuePosition}>
          {queue.indexOf(reviewTable) + 1} / {queue.length}
        </span>
      </div>
      <section aria-label="구역별 검토 현황" css={styles.reviewBoard}>
        <div css={styles.reviewHeader}>
          <div>
            <h3 css={styles.reviewTitle}>구역별 검토 현황</h3>
            <p css={styles.reviewDescription}>색깔로 상태를 확인하고 검토할 테이블을 선택하세요.</p>
          </div>
          <div css={styles.legend}>
            {(
              [
                [styles.passSwatch, "정상"],
                [styles.failSwatch, "이상"],
                [styles.reviewSwatch, "검토·오류"],
                [styles.pendingSwatch, "미제출"],
              ] as const
            ).map(([color, label]) => (
              <span key={label} css={styles.legendItem}>
                <i css={[styles.legendSwatch, color]} aria-hidden="true" />
                {label}
              </span>
            ))}
          </div>
        </div>
        <div css={styles.reviewAreaGrid}>
          {AREAS.map((area) => (
            <div key={area}>
              <div css={styles.reviewAreaTitle}>{area} 구역</div>
              <div css={styles.statusGrid}>
                {tables
                  .filter((table) => table.area === area)
                  .map((table) => {
                    const selectable = table.status === "REVIEW" || table.status === "ERROR";
                    return (
                      <button
                        key={table.id}
                        type="button"
                        aria-label={`${table.id} ${STATUS_INFO[table.status][0]}`}
                        aria-pressed={selectable && table.id === reviewTable.id}
                        title={`${table.id} · ${STATUS_INFO[table.status][0]}`}
                        disabled={!selectable}
                        onClick={() => onSelectTable(table.id)}
                        css={[
                          styles.reviewTableCell,
                          statusStyles[table.status],
                          selectable ? styles.selectableTableCell : null,
                          selectable && table.id === reviewTable.id ? styles.activeTableCell : null,
                        ]}
                      />
                    );
                  })}
              </div>
            </div>
          ))}
        </div>
      </section>
      <div css={styles.reviewDetailLayout}>
        <div css={styles.reviewPhotoCard}>
          <div css={styles.reviewTableHeader}>
            <h2>{reviewTable.id}</h2>
            <span>
              {reviewTable.area} 구역 · {formatDate(sessionDate)}
            </span>
          </div>
          <Photo table={reviewTable} large overlay={overlay} />
          <PhotoTabs overlay={overlay} onOverlayChange={onOverlayChange} />
        </div>
        <div css={styles.reviewResultCard}>
          <div css={styles.resultHeader}>
            AI 판독 <Badge status={reviewTable.status} />
          </div>
          <h2>{STATUS_INFO[reviewTable.status][0]}</h2>
          <p css={styles.reviewReason}>{reviewTable.reason}</p>
          {reviewTable.confidence != null && (
            <>
              <div css={styles.confidenceMeta}>
                <span>판독 신뢰도</span>
                <b>{Math.round(reviewTable.confidence * 100)}%</b>
              </div>
              <div css={styles.progressTrack} data-role="progress-track">
                <i style={{ width: `${reviewTable.confidence * 100}%` }} />
              </div>
            </>
          )}
          <div css={styles.reviewActions}>
            <InspectionActions
              table={reviewTable}
              closed={closed}
              reason={reason}
              onReasonChange={onReasonChange}
              onUpdate={onUpdate}
            />
          </div>
        </div>
      </div>
    </>
  );
}
