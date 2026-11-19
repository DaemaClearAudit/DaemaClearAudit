import * as styles from "../../styles";
import type { SerializedStyles } from "@emotion/react";
import { Image, ImagePlus } from "lucide-react";
import { STATUS_INFO } from "../../constants/inspection";
import type { Status, Table } from "../../types";
const badgeColors: Record<Status, SerializedStyles> = {
  PASS: styles.badgePass,
  FAIL: styles.badgeFail,
  REVIEW: styles.badgeReview,
  ERROR: styles.badgeFail,
  PENDING: styles.badgePending,
};
export const Badge = ({ status }: { status: Status }) => (
  <span css={[styles.badge, badgeColors[status]]}>{STATUS_INFO[status][0]}</span>
);
export function Photo({
  table,
  large = false,
  overlay = false,
}: {
  table: Table;
  large?: boolean;
  overlay?: boolean;
}) {
  return (
    <div
      css={[
        styles.photo,
        large ? styles.largePhoto : null,
        table.status === "PENDING" ? styles.pendingPhoto : null,
      ]}
      data-photo={large ? "large" : "default"}
    >
      <div css={styles.photoSymbol} data-photo="symbol">
        {table.status === "PENDING" ? (
          <ImagePlus aria-hidden="true" size={large ? 34 : 23} strokeWidth={1.5} />
        ) : (
          <Image aria-hidden="true" size={large ? 34 : 23} strokeWidth={1.5} />
        )}
      </div>
      <strong>
        {table.status === "PENDING" ? "아직 제출된 사진이 없어요" : "테이블 사진 예시"}
      </strong>
      <span>
        {table.status === "PENDING"
          ? "사진 제출을 기다리고 있습니다"
          : "실제 사진은 서버 연결 후 표시됩니다"}
      </span>
      {overlay && table.status === "FAIL" && (
        <div css={styles.detectionBox}>
          <span>감지 영역</span>
        </div>
      )}
    </div>
  );
}
