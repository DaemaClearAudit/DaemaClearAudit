import type { SerializedStyles } from "@emotion/react";
import { ArrowRight, Sparkles } from "lucide-react";
import * as styles from "../../styles";
import { counts, areaStatus } from "../../data";
import { AREAS } from "../../constants/inspection";
import type { Area, Status, Table } from "../../types";
import { Badge } from "../../components/inspection/InspectionVisuals";

interface DashboardPageProps {
  tables: Table[];
  onOpenManage: () => void;
  onSelectArea: (area: Area) => void;
}

const statusStyles: Record<Status, SerializedStyles> = {
  PASS: styles.miniPass,
  FAIL: styles.miniFail,
  REVIEW: styles.miniReview,
  ERROR: styles.miniFail,
  PENDING: styles.miniPending,
};

function activityStatuses(group: Table[]) {
  return Array.from({ length: 4 }, (_, index) => group[index]?.status ?? "PENDING");
}

export function DashboardPage({ tables, onOpenManage, onSelectArea }: DashboardPageProps) {
  return (
    <>
      <div css={styles.sectionHeading}>
        <div>
          <h2>구역별 현황</h2>
          <p>구역을 선택해 테이블별 점검 결과를 확인하세요.</p>
        </div>
        <button css={styles.textButton} onClick={onOpenManage}>
          전체 테이블 보기 <ArrowRight aria-hidden="true" size={13} css={styles.arrowIcon} />
        </button>
      </div>
      <div css={styles.areaGrid}>
        {AREAS.map((area) => {
          const group = tables.filter((table) => table.area === area);
          const count = counts(group);

          return (
            <button key={area} css={styles.areaCard} onClick={() => onSelectArea(area)}>
              <div css={styles.areaCardHeader}>
                <div>
                  <strong>{area} 구역</strong>
                </div>
                <Badge status={areaStatus(group)} />
              </div>
              <p>테이블 {4 - count.PENDING} / 4개 점검 완료</p>
              <div css={styles.areaActivityGrid} aria-label={`${area} 구역 진행 상태`}>
                {activityStatuses(group).map((status, index) => (
                  <span
                    key={`${area}-${index}`}
                    css={[styles.activityCell, statusStyles[status]]}
                    aria-hidden="true"
                  />
                ))}
              </div>
              <div css={styles.areaCardFooter}>
                <span>
                  정상 {count.PASS} · 이상 {count.FAIL} · 검토 {count.REVIEW + count.ERROR}
                </span>
                <b>
                  자세히 보기 <ArrowRight aria-hidden="true" size={12} css={styles.arrowIcon} />
                </b>
              </div>
            </button>
          );
        })}
      </div>
      <div css={styles.prototypeNotice}>
        <Sparkles aria-hidden="true" size={18} css={styles.noticeIcon} />
        <div>
          <b>이 화면은 시연용 프로토타입입니다.</b>
          <p>사진과 AI 판독 결과는 예시이며, 변경 사항은 현재 브라우저에 저장됩니다.</p>
        </div>
      </div>
    </>
  );
}
