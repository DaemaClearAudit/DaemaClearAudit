import { css } from "@emotion/react";

export const modalOverlay = css`
  position: fixed;
  inset: 0px;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgb(15 23 42 / 0.4);
  padding: 1rem;
`;

export const modal = css`
  width: 100%;
  max-width: 28rem;
  border-radius: 1rem;
  background-color: rgb(255 255 255);
  padding: 1.5rem;
  box-shadow: 0 25px 50px -12px rgb(0 0 0 / 0.25);
`;

export const modalHeader = css`
  margin-bottom: 17px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
`;

export const modalDescription = css`
  margin-top: 0.5rem;
  font-size: 0.75rem;
  line-height: 1rem;
  color: rgb(148 163 184);
`;

export const formLabel = css`
  margin-top: 1.5rem;
  display: block;
  font-size: 0.75rem;
  line-height: 1rem;
  font-weight: 700;
`;

export const formHint = css`
  margin-top: 0.5rem;
  font-size: 0.75rem;
  line-height: 1rem;
  line-height: 1.625;
  color: rgb(148 163 184);
`;

export const modalActions = css`
  margin-top: 25px;
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
`;
