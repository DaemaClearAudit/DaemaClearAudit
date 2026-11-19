import { css } from "@emotion/react";
import { ArrowUpRight, Check, CircleAlert, Clock3 } from "lucide-react";
import type { Status } from "../../types";
import * as styles from "../../styles";

const statColors = {
  green: css`
    background: #eaf9f3;
    color: #42ab85;
  `,
  red: css`
    background: #fff1f1;
    color: #e67578;
  `,
  amber: css`
    background: #fff8e8;
    color: #d9a446;
  `,
} as const;

interface InspectionStatsProps {
  c: Record<Status, number>;
}

export function InspectionStats({ c }: InspectionStatsProps) {
  const done = 16 - c.PENDING;
  const percent = Math.round((done / 16) * 100);
  const summaries = [
    ["정상", c.PASS, <Check aria-hidden="true" size={15} />, "green", "깨끗하게 완료"],
    ["이상", c.FAIL, <CircleAlert aria-hidden="true" size={15} />, "red", "확인이 필요해요"],
    [
      "검토 필요",
      c.REVIEW + c.ERROR,
      <Clock3 aria-hidden="true" size={15} />,
      "amber",
      "관리자 확인 대기",
    ],
  ] as const;

  return (
    <section css={styles.statsGrid}>
      <div css={styles.progressCard}>
        <div css={styles.statHeader}>
          전체 진행률 <ArrowUpRight aria-hidden="true" size={15} css={styles.accentIcon} />
        </div>
        <div css={styles.statValue}>
          {percent}
          <small>%</small> <em>{done} / 16 테이블</em>
        </div>
        <div css={styles.progressTrack} data-role="progress-track">
          <i style={{ width: `${percent}%` }} />
        </div>
      </div>
      {summaries.map(([label, n, icon, color, description]) => (
        <div css={styles.statCard} key={label}>
          <div css={styles.statHeader}>
            {label}
            <span css={[styles.statIcon, statColors[color]]}>{icon}</span>
          </div>
          <div css={styles.statValue}>
            {n}
            <small>개</small>
          </div>
          <p>{description}</p>
        </div>
      ))}
    </section>
  );
}
