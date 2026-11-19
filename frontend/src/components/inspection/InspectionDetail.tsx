import { RefreshCw, X } from "lucide-react";
import type { InspectionAction, Table } from "../../types";
import * as styles from "../../styles";
import { Badge, Photo } from "./InspectionVisuals";
import { formatDate } from "../../utils/formatDate";

interface PhotoTabsProps {
  overlay: boolean;
  onOverlayChange: (overlay: boolean) => void;
  modal?: boolean;
}

export function PhotoTabs({ overlay, onOverlayChange, modal = false }: PhotoTabsProps) {
  return (
    <div css={styles.photoTabs}>
      <button css={!overlay ? styles.photoTabActive : null} onClick={() => onOverlayChange(false)}>
        원본
      </button>
      <button css={overlay ? styles.photoTabActive : null} onClick={() => onOverlayChange(true)}>
        검출 표시
      </button>
      {modal && <span css={styles.photoTabMeta}>회차 3건</span>}
    </div>
  );
}

export interface InspectionActionsProps {
  table: Table;
  closed: boolean;
  reason: string;
  onReasonChange: (reason: string) => void;
  onUpdate: (table: Table, action: InspectionAction) => void;
  compact?: boolean;
}

export function InspectionActions({
  table,
  closed,
  reason,
  onReasonChange,
  onUpdate,
  compact = false,
}: InspectionActionsProps) {
  if (table.status === "PENDING" && !closed) {
    return (
      <>
        <div css={styles.actionTitle}>시연용 사진 제출</div>
        <p css={styles.actionHint}>실제 제출 연동 전, 예시 판독 결과를 생성합니다.</p>
        <button css={styles.submitButton} onClick={() => onUpdate(table, "submit")}>
          예시 사진 제출 및 판독
        </button>
      </>
    );
  }

  const disabled = closed || table.status === "PENDING";
  return (
    <>
      <div css={styles.actionTitle}>관리자 조치</div>
      <div css={styles.actionButtonGroup}>
        <button
          css={styles.secondaryButton}
          disabled={disabled}
          onClick={() => onUpdate(table, "PASS")}
        >
          정상으로 수정
        </button>
        <button
          css={styles.primaryButton}
          disabled={disabled}
          onClick={() => onUpdate(table, "FAIL")}
        >
          이상 확정
        </button>
      </div>
      <button
        css={styles.fullSecondaryButton}
        disabled={disabled}
        onClick={() => onUpdate(table, "reprocess")}
      >
        <RefreshCw aria-hidden="true" size={14} css={styles.iconMargin} /> 재판독 요청
      </button>
      {!compact && (
        <>
          <label css={styles.visuallyHidden} htmlFor="reason">
            수정 사유
          </label>
          <input
            id="reason"
            css={styles.textInput}
            placeholder="수정 사유 입력 (선택)"
            value={reason}
            onChange={(event) => onReasonChange(event.target.value)}
            disabled={disabled}
          />
          <p css={styles.actionHint}>
            {closed
              ? "종료된 회차는 수정할 수 없습니다."
              : "시연용 동작이며 실제 서버에 전송되지 않습니다."}
          </p>
        </>
      )}
    </>
  );
}

interface InspectionDetailProps extends InspectionActionsProps, PhotoTabsProps {
  sessionDate: string;
  onClose: () => void;
  modal?: boolean;
}

export function InspectionDetail({
  table,
  closed,
  reason,
  onReasonChange,
  onUpdate,
  overlay,
  onOverlayChange,
  sessionDate,
  onClose,
  modal = false,
}: InspectionDetailProps) {
  const content = (
    <aside css={modal ? styles.detailModal : styles.detailPanel}>
      <div css={styles.detailHeader}>
        <div>
          <h2>{table.id}</h2>
          <p>
            {table.area} 구역 · {formatDate(sessionDate)}
          </p>
        </div>
        <button css={styles.closeButton} onClick={onClose} aria-label="상세 닫기">
          <X aria-hidden="true" size={20} />
        </button>
      </div>
      <Photo table={table} large overlay={overlay} />
      <PhotoTabs overlay={overlay} onOverlayChange={onOverlayChange} modal={modal} />
      <div css={styles.detailSection} data-detail-section={modal ? "modal" : undefined}>
        <div css={styles.resultHeader}>
          AI 판독 <Badge status={table.status} />
        </div>
        <div css={styles.resultReason}>
          {table.reason || "사진이 제출되면 판독 결과가 표시됩니다."}
        </div>
        {!modal && table.confidence != null && (
          <>
            <div css={styles.confidenceMeta}>
              <span>판독 신뢰도</span>
              <b>{Math.round(table.confidence * 100)}%</b>
            </div>
            <div css={styles.progressTrack} data-role="progress-track">
              <i style={{ width: `${table.confidence * 100}%` }} />
            </div>
          </>
        )}
      </div>
      <div css={styles.detailSection} data-detail-section={modal ? "modal" : undefined}>
        <InspectionActions
          table={table}
          closed={closed}
          reason={reason}
          onReasonChange={onReasonChange}
          onUpdate={onUpdate}
          compact={modal}
        />
      </div>
      {modal ? (
        <div css={styles.modalNavigation}>
          <span>← A-03</span>
          <span>{table.area} 내 이동</span>
          <span>A-05 →</span>
        </div>
      ) : (
        <div css={styles.historySection}>
          <div css={styles.actionTitle}>처리 이력</div>
          {table.history.length ? (
            [...table.history].reverse().map((entry, index) => (
              <p key={index}>
                <span>{entry.time}</span> {entry.text}
              </p>
            ))
          ) : (
            <p>아직 처리 이력이 없습니다.</p>
          )}
        </div>
      )}
    </aside>
  );

  if (!modal) return content;

  return (
    <div
      css={styles.detailOverlay}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      {content}
    </div>
  );
}
