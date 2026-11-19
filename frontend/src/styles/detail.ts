import { css } from "@emotion/react";

export const photoTabs = css`
  margin-top: 0.75rem;
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  & button {
    border-radius: 0.375rem;
    border-width: 1px;
    border-color: rgb(226 234 243);
    background-color: rgb(255 255 255);
    padding-left: 9px;
    padding-right: 9px;
    padding-top: 7px;
    padding-bottom: 7px;
    font-size: 10px;
    font-weight: 700;
    color: rgb(140 155 176);
  }
`;

export const photoTabActive = css`
  border-color: rgb(188 208 251) !important;
  background-color: rgb(237 243 255) !important;
  color: rgb(68 121 228) !important;
`;

export const photoTabMeta = css`
  align-self: center;
  margin-left: auto;
  font-size: 10px;
  color: rgb(143 158 179);
`;

export const actionTitle = css`
  margin-bottom: 0.625rem;
  font-size: 11px;
  font-weight: 700;
  color: rgb(140 157 177);
`;

export const actionHint = css`
  margin-top: 0.5rem;
  font-size: 10px;
  line-height: 1.6;
  color: rgb(166 179 194);
`;

export const submitButton = css`
  margin-top: 7px;
  display: inline-flex;
  min-height: 39px;
  width: 100%;
  align-items: center;
  justify-content: center;
  border-radius: 0.5rem;
  border-width: 1px;
  border-color: rgb(220 229 240);
  border-color: rgb(50 111 233);
  background-color: rgb(50 111 233);
  padding-top: 0.625rem;
  padding-bottom: 0.625rem;
  padding-left: 5px;
  padding-right: 5px;
  padding-top: 9px;
  padding-bottom: 9px;
  font-size: 0.75rem;
  line-height: 1rem;
  font-size: 11px;
  font-weight: 700;
  color: rgb(255 255 255);
  box-shadow: 0 4px 10px #326fe91b;
  &:hover:enabled {
    filter: brightness(0.97);
  }
  &:disabled {
    cursor: not-allowed;
    opacity: 0.45;
  }
`;

export const actionButtonGroup = css`
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 7px;
  & button {
    padding-left: 5px;
    padding-right: 5px;
    padding-top: 9px;
    padding-bottom: 9px;
    font-size: 11px;
  }
`;

export const secondaryButton = css`
  display: inline-flex;
  min-height: 39px;
  align-items: center;
  justify-content: center;
  border-radius: 0.5rem;
  border-width: 1px;
  border-color: rgb(220 229 240);
  background-color: rgb(255 255 255);
  padding-left: 15px;
  padding-right: 15px;
  padding-top: 0.625rem;
  padding-bottom: 0.625rem;
  font-size: 0.75rem;
  line-height: 1rem;
  font-weight: 700;
  color: rgb(101 118 141);
  &:hover:enabled {
    filter: brightness(0.97);
  }
  &:disabled {
    cursor: not-allowed;
    opacity: 0.45;
  }
`;

export const primaryButton = css`
  display: inline-flex;
  min-height: 39px;
  align-items: center;
  justify-content: center;
  border-radius: 0.5rem;
  border-width: 1px;
  border-color: rgb(220 229 240);
  border-color: rgb(50 111 233);
  background-color: rgb(50 111 233);
  padding-left: 15px;
  padding-right: 15px;
  padding-top: 0.625rem;
  padding-bottom: 0.625rem;
  font-size: 0.75rem;
  line-height: 1rem;
  font-weight: 700;
  color: rgb(255 255 255);
  box-shadow: 0 4px 10px #326fe91b;
  &:hover:enabled {
    filter: brightness(0.97);
  }
  &:disabled {
    cursor: not-allowed;
    opacity: 0.45;
  }
`;

export const fullSecondaryButton = css`
  margin-top: 7px;
  display: inline-flex;
  min-height: 39px;
  width: 100%;
  align-items: center;
  justify-content: center;
  border-radius: 0.5rem;
  border-width: 1px;
  border-color: rgb(220 229 240);
  background-color: rgb(255 255 255);
  padding-top: 0.625rem;
  padding-bottom: 0.625rem;
  padding-left: 5px;
  padding-right: 5px;
  padding-top: 9px;
  padding-bottom: 9px;
  font-size: 0.75rem;
  line-height: 1rem;
  font-size: 11px;
  font-weight: 700;
  color: rgb(101 118 141);
  &:hover:enabled {
    filter: brightness(0.97);
  }
  &:disabled {
    cursor: not-allowed;
    opacity: 0.45;
  }
`;

export const iconMargin = css`
  margin-right: 0.375rem;
`;

export const visuallyHidden = css`
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
`;

export const textInput = css`
  margin-top: 0.5rem;
  width: 100%;
  border-radius: 7px;
  border-width: 1px;
  border-color: rgb(228 235 243);
  padding: 11px;
  font-size: 11px;
  color: rgb(82 99 123);
  outline: 2px solid transparent;
  outline-offset: 2px;
  &:focus {
    border-color: rgb(111 155 241);
  }
`;

export const detailPanel = css`
  order: -9999;
  width: 100%;
  align-self: stretch;
  border-radius: 11px;
  border-width: 1px;
  border-color: rgb(228 235 244);
  background-color: rgb(255 255 255);
  padding: 18px;
  @media (min-width: 1101px) {
    & {
      order: 0;
      align-self: flex-start;
    }
  }
`;

export const detailOverlay = css`
  position: fixed;
  inset: 0;
  z-index: 40;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgb(15 23 42 / 0.32);
  padding: 16px;
`;

export const detailModal = css`
  width: min(100%, 400px);
  max-height: calc(100vh - 32px);
  overflow-y: auto;
  border-radius: 10px;
  border-width: 1px;
  border-color: rgb(218 228 240);
  background-color: rgb(255 255 255);
  padding: 14px;
  box-shadow: 0 18px 45px rgb(41 73 125 / 0.18);
  & [data-photo="large"] {
    height: 145px;
  }
  & [data-detail-section="modal"] {
    margin-top: 10px;
    padding-top: 10px;
  }
  & [data-detail-section="modal"] button {
    min-height: 33px;
    padding-top: 6px;
    padding-bottom: 6px;
  }
`;

export const detailHeader = css`
  margin-bottom: 17px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  & p {
    margin-top: 5px;
    font-size: 10px;
    color: rgb(161 174 191);
  }
`;

export const closeButton = css`
  border-width: 0px;
  background-color: transparent;
  font-size: 23px;
  line-height: 1;
  color: rgb(165 178 193);
`;

export const detailSection = css`
  margin-top: 18px;
  border-top-width: 1px;
  border-color: rgb(237 241 246);
  padding-top: 18px;
`;

export const resultHeader = css`
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  font-weight: 700;
  color: rgb(147 162 181);
`;

export const resultReason = css`
  margin-top: 0.875rem;
  margin-bottom: 0.875rem;
  border-left-width: 2px;
  border-color: rgb(120 162 247);
  padding-top: 5px;
  padding-bottom: 5px;
  padding-left: 0.625rem;
  font-size: 11px;
  line-height: 1.7;
  color: rgb(82 101 125);
`;

export const confidenceMeta = css`
  margin-bottom: 7px;
  margin-top: 0.875rem;
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: rgb(154 169 185);
  & b {
    color: rgb(96 118 146);
  }
`;

export const progressTrack = css`
  height: 0.375rem;
  overflow: hidden;
  border-radius: 9px;
  background-color: rgb(237 241 247);
  & i {
    display: block;
    height: 100%;
    border-radius: 9px;
    background-color: rgb(74 128 241);
  }
`;

export const historySection = css`
  margin-top: 18px;
  border-top-width: 1px;
  border-color: rgb(237 241 246);
  padding-top: 18px;
  & p {
    margin-top: 0.5rem;
    font-size: 10px;
    line-height: 1.6;
    color: rgb(166 179 194);
  }
  & p span {
    margin-right: 5px;
  }
`;

export const modalNavigation = css`
  display: flex;
  justify-content: space-between;
  margin-top: 18px;
  border-top-width: 1px;
  border-color: rgb(237 241 246);
  padding-top: 14px;
  font-size: 10px;
  color: rgb(119 139 165);
`;

export const photo = css`
  position: relative;
  display: flex;
  min-height: 112px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  overflow: hidden;
  background-color: rgb(237 243 250);
  text-align: center;
  color: rgb(154 174 198);
  & span {
    font-size: 9px;
    color: rgb(180 193 208);
  }
  & strong {
    font-size: 10px;
    font-weight: 600;
  }
`;

export const largePhoto = css`
  height: 195px;
  border-radius: 0.5rem;
  & [data-photo="symbol"] {
    font-size: 38px;
  }
`;

export const pendingPhoto = css`
  background-color: rgb(246 248 251) !important;
`;

export const photoSymbol = css`
  font-size: 25px;
  color: rgb(183 200 220);
`;

export const detectionBox = css`
  position: absolute;
  left: 37%;
  top: 31%;
  height: 39%;
  width: 28%;
  border-radius: 0.125rem;
  border-width: 1px;
  border-color: rgb(99 144 237);
  & span {
    position: absolute;
    left: -1px;
    top: -19px;
    border-radius: 0.25rem;
    background-color: rgb(93 137 228);
    padding-left: 0.375rem;
    padding-right: 0.375rem;
    padding-top: 3px;
    padding-bottom: 3px;
    font-size: 9px;
    color: rgb(255 255 255);
  }
`;
