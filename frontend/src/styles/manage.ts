import { css } from "@emotion/react";

export const manageLayout = css`
  margin-top: 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  @media (min-width: 1101px) {
    & {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 310px;
    }
  }
`;

export const managePanel = css`
  min-width: 0px;
`;

export const manageHeader = css`
  margin-bottom: 17px;
  margin-bottom: 1.25rem;
  margin-top: 0px;
  display: flex;
  flex-direction: column;
  flex-wrap: wrap;
  align-items: flex-start;
  align-items: flex-end;
  justify-content: space-between;
  gap: 0.75rem;
  @media (min-width: 768px) {
    & {
      flex-direction: row;
      align-items: flex-end;
    }
  }
  & p {
    margin-top: 7px;
    font-size: 0.75rem;
    line-height: 1rem;
    color: rgb(147 161 180);
  }
`;

export const searchField = css`
  width: 100%;
  border-radius: 0.5rem;
  border-width: 1px;
  border-color: rgb(226 234 244);
  background-color: rgb(255 255 255);
  padding-left: 0.625rem;
  padding-right: 0.625rem;
  padding-top: 7px;
  padding-bottom: 7px;
  color: rgb(157 174 194);
  @media (min-width: 768px) {
    & {
      width: auto;
    }
  }
  & input {
    width: 90%;
    border-width: 0px;
    font-size: 11px;
    color: rgb(78 97 122);
    outline: 2px solid transparent;
    outline-offset: 2px;
  }
  @media (min-width: 768px) {
    & input {
      width: 130px;
    }
  }
`;

export const inputIcon = css`
  margin-right: 0.25rem;
  display: inline-block;
  vertical-align: -3px;
`;

export const areaTabs = css`
  margin-bottom: 15px;
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  border-bottom-width: 1px;
  border-color: rgb(229 235 243);
  & button {
    border-width: 0px;
    border-bottom-width: 2px;
    border-color: transparent;
    background-color: transparent;
    padding-left: 13px;
    padding-right: 13px;
    padding-top: 11px;
    padding-bottom: 11px;
    font-size: 0.75rem;
    line-height: 1rem;
    font-weight: 700;
    color: rgb(145 160 180);
  }
`;

export const areaTabActive = css`
  border-color: rgb(50 111 233) !important;
  color: rgb(50 111 233) !important;
`;

export const filterTabs = css`
  margin-bottom: 1rem;
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
`;

export const filterButton = css`
  border-radius: 7px;
  border-width: 1px;
  border-color: rgb(230 237 245);
  background-color: rgb(255 255 255);
  padding-left: 0.625rem;
  padding-right: 0.625rem;
  padding-top: 7px;
  padding-bottom: 7px;
  font-size: 10px;
  font-weight: 700;
  color: rgb(140 155 173);
  & span {
    margin-left: 3px;
  }
`;

export const filterButtonActive = css`
  border-color: rgb(219 231 255) !important;
  background-color: rgb(237 243 255) !important;
  color: rgb(54 113 232) !important;
`;

export const tableGrid = css`
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  @media (min-width: 1280px) {
    & {
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }
  }
`;

export const tableCard = css`
  overflow: hidden;
  border-radius: 10px;
  border-width: 1px;
  border-color: rgb(229 235 243);
  background-color: rgb(255 255 255);
  padding: 0px;
  text-align: left;
  color: inherit;
  &:hover {
    border-color: rgb(158 188 247);
    box-shadow: 0 8px 25px #4473ba0d;
  }
`;

export const tableCardActive = css`
  border-color: rgb(93 141 240) !important;
  box-shadow: 0 0 0 1px #5d8df0;
`;

export const tableCardBody = css`
  padding: 0.75rem;
  & > div {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 3px;
  }
  & p {
    margin-top: 9px;
    font-size: 10px;
    color: rgb(169 182 196);
  }
  & strong {
    font-size: 0.75rem;
    line-height: 1rem;
  }
`;

export const emptyState = css`
  grid-column: 1 / -1;
  padding: 55px;
  text-align: center;
  font-size: 0.75rem;
  line-height: 1rem;
  color: rgb(161 175 191);
`;

export const tableCount = css`
  margin: 18px;
  text-align: center;
  font-size: 10px;
  color: rgb(167 180 196);
`;

export const openDetailsButton = css`
  align-self: flex-start;
  border-radius: 0.5rem;
  border-width: 1px;
  border-color: rgb(220 230 243);
  background-color: rgb(255 255 255);
  padding: 0.625rem;
  color: rgb(107 134 177);
`;

export const reviewEmpty = css`
  padding-left: 1.25rem;
  padding-right: 1.25rem;
  padding-top: 85px;
  padding-bottom: 85px;
  text-align: center;
  & > div {
    margin-left: auto;
    margin-right: auto;
    margin-bottom: 1rem;
    display: grid;
    height: 50px;
    width: 50px;
    place-items: center;
    border-radius: 9999px;
    background-color: rgb(234 248 242);
    font-size: 23px;
    color: rgb(66 171 133);
  }
  & p {
    margin-bottom: 22px;
    margin-top: 0.625rem;
    font-size: 0.75rem;
    line-height: 1rem;
    color: rgb(155 170 189);
  }
`;

export const queuePosition = css`
  font-size: 0.75rem;
  line-height: 1rem;
  color: rgb(146 161 180);
`;

export const reviewBoard = css`
  margin-bottom: 1rem;
  border-radius: 0.75rem;
  border-width: 1px;
  border-color: rgb(229 236 245);
  background-color: rgb(255 255 255);
  padding: 1rem;
  @media (min-width: 640px) {
    & {
      padding: 1.25rem;
    }
  }
`;

export const reviewHeader = css`
  margin-bottom: 1rem;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
`;

export const reviewTitle = css`
  font-size: 0.875rem;
  line-height: 1.25rem;
  font-weight: 700;
  color: rgb(38 56 80);
`;

export const reviewDescription = css`
  margin-top: 0.25rem;
  font-size: 11px;
  color: rgb(147 161 180);
`;

export const legend = css`
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  font-size: 10px;
  color: rgb(128 144 165);
`;

export const reviewAreaGrid = css`
  display: flex;
  flex-wrap: wrap;
  column-gap: 2rem;
  row-gap: 1rem;
`;

export const reviewAreaTitle = css`
  margin-bottom: 0.5rem;
  font-size: 11px;
  font-weight: 700;
  color: rgb(104 125 152);
`;

export const reviewTableCell = css`
  height: 1.75rem;
  width: 1.75rem;
  border-radius: 4px;
  transition-property:
    color, background-color, border-color, text-decoration-color, fill, stroke, opacity, box-shadow,
    transform, filter, backdrop-filter;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
  &:focus-visible {
    outline-style: solid;
    outline-width: 2px;
    outline-offset: 2px;
    outline-color: #326fe9;
  }
  &:disabled {
    cursor: default;
  }
`;

export const selectableTableCell = css`
  cursor: pointer;
  &:hover {
    filter: brightness(0.95);
  }
`;

export const activeTableCell = css`
  box-shadow:
    0 0 0 2px #ffffff,
    0 0 0 4px #326fe9;
`;

export const reviewDetailLayout = css`
  display: grid;
  grid-template-columns: repeat(1, minmax(0, 1fr));
  gap: 1rem;
  @media (min-width: 1101px) {
    & {
      grid-template-columns: minmax(0, 1.5fr) minmax(250px, 1fr);
    }
  }
`;

export const reviewPhotoCard = css`
  border-radius: 11px;
  border-width: 1px;
  border-color: rgb(230 237 245);
  background-color: rgb(255 255 255);
  padding: 1.25rem;
  & [data-photo="large"] {
    height: 240px;
  }
  @media (min-width: 768px) {
    & [data-photo="large"] {
      height: 320px;
    }
  }
`;

export const reviewTableHeader = css`
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.625rem;
  & span {
    font-size: 11px;
    color: rgb(164 176 190);
  }
`;

export const reviewResultCard = css`
  border-radius: 11px;
  border-width: 1px;
  border-color: rgb(230 237 245);
  background-color: rgb(255 255 255);
  padding: 1.25rem;
  & > h2 {
    margin-top: 15px;
    margin-bottom: 15px;
    font-size: 22px;
  }
`;

export const reviewReason = css`
  min-height: 60px;
  font-size: 0.75rem;
  line-height: 1rem;
  line-height: 1.7;
  color: rgb(102 122 146);
`;

export const reviewActions = css`
  margin-top: 1.75rem;
`;
