import { css } from "@emotion/react";

export const miniPass = css`
  background-color: rgb(91 190 156);
  color: rgb(101 185 154);
`;

export const miniFail = css`
  background-color: rgb(231 139 147);
  color: rgb(223 146 147);
`;

export const miniReview = css`
  background-color: rgb(232 188 96);
  color: rgb(203 164 91);
`;

export const miniPending = css`
  background-color: rgb(177 193 214);
  color: rgb(166 179 195);
`;

export const passSwatch = css`
  background-color: rgb(112 191 162);
`;

export const failSwatch = css`
  background-color: rgb(233 152 154);
`;

export const reviewSwatch = css`
  background-color: rgb(231 189 105);
`;

export const pendingSwatch = css`
  background-color: rgb(232 237 243);
`;

export const legendItem = css`
  display: flex;
  align-items: center;
  gap: 0.375rem;
`;

export const legendSwatch = css`
  height: 0.625rem;
  width: 0.625rem;
  border-radius: 0.125rem;
`;

export const badgePass = css`
  background-color: rgb(234 248 242);
  color: rgb(53 166 125);
`;

export const badgeFail = css`
  background-color: rgb(255 240 240);
  color: rgb(211 109 112);
`;

export const badgeReview = css`
  background-color: rgb(255 246 228);
  color: rgb(187 139 48);
`;

export const badgePending = css`
  background-color: rgb(240 243 247);
  color: rgb(152 166 184);
`;

export const badge = css`
  display: inline-block;
  white-space: nowrap;
  border-radius: 0.375rem;
  padding-left: 0.5rem;
  padding-right: 0.5rem;
  padding-top: 5px;
  padding-bottom: 5px;
  font-size: 10px;
  font-weight: 700;
`;
