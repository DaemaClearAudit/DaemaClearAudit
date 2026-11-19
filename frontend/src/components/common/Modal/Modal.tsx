import type { ReactNode } from "react";
import { X } from "lucide-react";
import * as styles from "../../../styles";

interface ModalProps {
  open: boolean;
  title: string;
  description: string;
  onClose: () => void;
  children: ReactNode;
}

export function Modal({ open, title, description, onClose, children }: ModalProps) {
  if (!open) return null;

  return (
    <div
      css={styles.modalOverlay}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div role="dialog" aria-modal="true" aria-labelledby="modal-title" css={styles.modal}>
        <div css={styles.modalHeader}>
          <div>
            <h2 id="modal-title">{title}</h2>
            <p css={styles.modalDescription}>{description}</p>
          </div>
          <button type="button" css={styles.closeButton} onClick={onClose} aria-label="닫기">
            <X aria-hidden="true" size={20} />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
