import { css } from "@emotion/react";

export const statsGrid = css`
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.5rem;
  @media (min-width: 1000px) {
    & {
      grid-template-columns: 1.5fr repeat(3, minmax(0, 1fr));
      gap: 0.75rem;
    }
  }
`;

export const progressCard = css`
  min-height: 105px;
  border-radius: 11px;
  border-width: 1px;
  border-color: rgb(231 237 245);
  background-color: rgb(255 255 255);
  padding: 0.875rem;
  @media (min-width: 768px) {
    & {
      min-height: 120px;
      padding-left: 1.25rem;
      padding-right: 1.25rem;
      padding-top: 18px;
      padding-bottom: 18px;
    }
  }
  & [data-role="progress-track"] {
    margin-top: 15px;
  }
  & p {
    margin-top: 0.25rem;
    font-size: 10px;
    color: rgb(168 181 196);
  }
`;

export const statHeader = css`
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  font-weight: 700;
  color: rgb(137 155 177);
`;

export const accentIcon = css`
  color: rgb(143 170 240);
`;

export const statValue = css`
  margin-top: 9px;
  font-size: 23px;
  font-weight: 800;
  line-height: 1.3;
  color: rgb(38 56 80);
  @media (min-width: 768px) {
    & {
      font-size: 27px;
    }
  }
  & em {
    margin-left: 0.5rem;
    white-space: nowrap;
    font-size: 11px;
    font-weight: 500;
    font-style: normal;
    color: rgb(160 173 188);
  }
  @media (max-width: 380px) {
    & em {
      margin-left: 0px;
      display: block;
    }
  }
  & small {
    margin-left: 3px;
    font-size: 0.75rem;
    line-height: 1rem;
    color: rgb(160 173 188);
  }
`;

export const statCard = css`
  min-height: 105px;
  border-radius: 11px;
  border-width: 1px;
  border-color: rgb(231 237 245);
  background-color: rgb(255 255 255);
  padding: 0.875rem;
  @media (min-width: 768px) {
    & {
      min-height: 120px;
      padding-left: 1.25rem;
      padding-right: 1.25rem;
      padding-top: 18px;
      padding-bottom: 18px;
    }
  }
  & p {
    margin-top: 0.25rem;
    font-size: 10px;
    color: rgb(168 181 196);
  }
`;

export const statIcon = css`
  display: grid;
  height: 25px;
  width: 25px;
  place-items: center;
  border-radius: 7px;
  font-size: 13px;
`;

export const header = css`
  display: flex;
  height: 60px;
  align-items: center;
  justify-content: space-between;
  border-bottom-width: 1px;
  border-color: rgb(229 235 243);
  background-color: rgb(255 255 255);
  padding-left: 1rem;
  padding-right: 1rem;
  @media (min-width: 768px) {
    & {
      height: 72px;
      padding-left: 2rem;
      padding-right: 2rem;
    }
  }
`;

export const brand = css`
  display: flex;
  align-items: center;
  gap: 0.625rem;
  & b {
    display: block;
    font-size: 17px;
    letter-spacing: -0.5px;
  }
  & small {
    margin-top: 1px;
    display: block;
    font-size: 10px;
    color: rgb(154 168 186);
  }
`;

export const brandMark = css`
  display: grid;
  height: 2.25rem;
  width: 2.25rem;
  place-items: center;
  border-radius: 11px;
  background-color: rgb(40 103 232);
  font-size: 21px;
  color: rgb(255 255 255);
`;

export const headerMeta = css`
  display: flex;
  align-items: center;
  gap: 22px;
`;

export const prototypeLabel = css`
  font-size: 10px;
  color: rgb(114 132 159);
  @media (max-width: 380px) {
    & {
      display: none;
    }
  }
  @media (min-width: 768px) {
    & {
      font-size: 0.75rem;
      line-height: 1rem;
    }
  }
`;

export const statusDot = css`
  margin-right: 5px;
  display: inline-block;
  height: 7px;
  width: 7px;
  border-radius: 9999px;
  background-color: rgb(81 191 153);
`;

export const userAvatar = css`
  display: grid;
  height: 34px;
  width: 34px;
  place-items: center;
  border-radius: 9999px;
  background-color: rgb(232 239 255);
  font-size: 0.75rem;
  line-height: 1rem;
  font-weight: 700;
  color: rgb(68 116 216);
`;

export const appLayout = css`
  min-height: calc(100vh - 72px);
  @media (min-width: 768px) {
    & {
      display: flex;
    }
  }
`;

export const sidebar = css`
  flex-shrink: 0;
  border-bottom-width: 1px;
  border-color: rgb(229 235 243);
  background-color: rgb(255 255 255);
  padding-left: 0.75rem;
  padding-right: 0.75rem;
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
  @media (min-width: 768px) {
    & {
      display: flex;
      width: 180px;
      flex-direction: column;
      border-bottom-width: 0px;
      border-right-width: 1px;
      padding-left: 15px;
      padding-right: 15px;
      padding-top: 34px;
      padding-bottom: 34px;
    }
  }
  @media (min-width: 1101px) {
    & {
      width: 215px;
    }
  }
  & nav {
    display: flex;
    gap: 0.25rem;
  }
  @media (min-width: 768px) {
    & nav {
      display: grid;
      gap: 5px;
    }
  }
`;

export const workspaceLabel = css`
  margin-bottom: 15px;
  display: none;
  padding-left: 0.875rem;
  padding-right: 0.875rem;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 1.2px;
  color: rgb(156 174 196);
  @media (min-width: 768px) {
    & {
      display: block;
    }
  }
`;

export const navItem = css`
  flex: 1 1 0%;
  border-radius: 9px;
  border-width: 0px;
  background-color: transparent;
  padding-left: 3px;
  padding-right: 3px;
  padding-top: 9px;
  padding-bottom: 9px;
  text-align: center;
  font-size: 11px;
  font-weight: 600;
  color: rgb(116 132 154);
  @media (min-width: 768px) {
    & {
      padding-left: 0.875rem;
      padding-right: 0.875rem;
      padding-top: 13px;
      padding-bottom: 13px;
      text-align: left;
      font-size: 13px;
    }
  }
  & em {
    margin-left: 3px;
    border-radius: 5px;
    background-color: rgb(237 242 250);
    padding-left: 0.375rem;
    padding-right: 0.375rem;
    padding-top: 1px;
    padding-bottom: 1px;
    font-size: 11px;
    font-style: normal;
    color: rgb(122 139 164);
  }
  @media (min-width: 768px) {
    & em {
      float: right;
    }
  }
  & span {
    margin-right: 0.25rem;
    font-size: 13px;
  }
  @media (min-width: 768px) {
    & span {
      margin-right: 0px;
      display: inline-block;
      width: 27px;
      font-size: 17px;
    }
  }
`;

export const navItemActive = css`
  background-color: rgb(237 243 255) !important;
  color: rgb(40 103 232) !important;
`;

export const navIcon = css`
  display: inline-block;
  vertical-align: -3px;
`;

export const sidebarNote = css`
  margin-top: auto;
  display: none;
  border-radius: 0.75rem;
  background-color: rgb(243 247 255);
  padding: 1rem;
  font-size: 0.75rem;
  line-height: 1rem;
  color: rgb(82 108 150);
  @media (min-width: 768px) {
    & {
      display: block;
    }
  }
  & p {
    margin-top: 0.75rem;
    font-size: 11px;
    line-height: 1.7;
    color: rgb(145 161 184);
  }
`;

export const sidebarNoteIcon = css`
  margin-bottom: 0.75rem;
  font-size: 1.25rem;
  line-height: 1.75rem;
  color: rgb(64 120 234);
`;

export const mainContent = css`
  margin-left: auto;
  margin-right: auto;
  min-width: 0px;
  max-width: 1700px;
  flex: 1 1 0%;
  padding-left: 1rem;
  padding-right: 1rem;
  padding-bottom: 50px;
  padding-top: 25px;
  @media (min-width: 768px) {
    & {
      padding-left: 25px;
      padding-right: 25px;
      padding-bottom: 70px;
      padding-top: 30px;
    }
  }
  @media (min-width: 1101px) {
    & {
      padding-left: 42px;
      padding-right: 42px;
      padding-top: 37px;
    }
  }
  & h1 {
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -1.1px;
  }
  & h2 {
    font-size: 17px;
    font-weight: 700;
    letter-spacing: -0.5px;
  }
`;

export const pageHeader = css`
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.25rem;
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

export const pageEyebrow = css`
  margin-bottom: 7px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 1.2px;
  color: rgb(112 149 221);
`;

export const sessionControls = css`
  display: flex;
  width: 100%;
  align-items: center;
  gap: 0.5rem;
  @media (max-width: 380px) {
    & {
      flex-wrap: wrap;
    }
  }
  @media (min-width: 768px) {
    & {
      width: auto;
    }
  }
  & select {
    min-height: 39px;
    min-width: 0px;
    flex: 1 1 0%;
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
    color: rgb(82 99 123);
  }
  @media (min-width: 768px) {
    & select {
      max-width: 190px;
    }
  }
`;

export const smallIcon = css`
  margin-right: 0.25rem;
`;

export const sessionBanner = css`
  margin-bottom: 17px;
  margin-top: 19px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-radius: 10px;
  border-width: 1px;
  border-color: rgb(231 237 245);
  background-color: rgb(255 255 255);
  padding-left: 18px;
  padding-right: 18px;
  padding-top: 0.875rem;
  padding-bottom: 0.875rem;
  font-size: 0.75rem;
  line-height: 1rem;
  color: rgb(149 163 181);
  @media (min-width: 768px) {
    & {
      margin-top: 26px;
    }
  }
  & > div {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.375rem;
  }
  @media (min-width: 768px) {
    & > div {
      gap: 0.75rem;
    }
  }
  & b {
    font-size: 0.75rem;
    line-height: 1rem;
    color: rgb(52 71 97);
  }
`;

export const calendarIcon = css`
  font-size: 1rem;
  line-height: 1.5rem;
  color: rgb(77 127 232);
`;

export const sessionState = css`
  border-radius: 5px;
  background-color: rgb(233 248 242);
  padding-left: 0.5rem;
  padding-right: 0.5rem;
  padding-top: 0.25rem;
  padding-bottom: 0.25rem;
  font-size: 10px;
  font-weight: 700;
  color: rgb(50 167 121);
`;

export const closedSessionState = css`
  background-color: rgb(237 241 246) !important;
  color: rgb(137 152 170) !important;
`;

export const sessionToggle = css`
  flex-shrink: 0;
  white-space: nowrap;
  border-width: 0px;
  background-color: transparent;
  font-size: 0.75rem;
  line-height: 1rem;
  font-weight: 700;
  color: rgb(66 121 228);
`;

export const arrowIcon = css`
  margin-left: 0.25rem;
  display: inline-block;
  vertical-align: -2px;
`;

export const statusMessage = css`
  margin-top: 0.875rem;
  margin-bottom: 0.875rem;
  display: flex;
  justify-content: space-between;
  border-radius: 0.5rem;
  border-width: 1px;
  border-color: rgb(215 230 255);
  background-color: rgb(234 242 255);
  padding-left: 15px;
  padding-right: 15px;
  padding-top: 0.75rem;
  padding-bottom: 0.75rem;
  font-size: 0.75rem;
  line-height: 1rem;
  color: rgb(66 115 201);
  & button {
    border-width: 0px;
    background-color: transparent;
    color: inherit;
  }
`;

export const sectionHeading = css`
  margin-bottom: 17px;
  margin-top: 35px;
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 0.75rem;
  & p {
    margin-top: 7px;
    font-size: 0.75rem;
    line-height: 1rem;
    color: rgb(147 161 180);
  }
`;

export const textButton = css`
  white-space: nowrap;
  border-width: 0px;
  background-color: transparent;
  font-size: 0.75rem;
  line-height: 1rem;
  font-weight: 700;
  color: rgb(66 121 228);
`;

export const areaGrid = css`
  display: grid;
  grid-template-columns: repeat(1, minmax(0, 1fr));
  gap: 0.75rem;
  @media (min-width: 380px) {
    & {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }
  @media (min-width: 768px) {
    & {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
  }
`;

export const areaCard = css`
  border-radius: 0.75rem;
  border-width: 1px;
  border-color: rgb(229 236 245);
  background-color: rgb(255 255 255);
  padding: 0.875rem;
  text-align: left;
  color: inherit;
  transition-property:
    color, background-color, border-color, text-decoration-color, fill, stroke, opacity, box-shadow,
    transform, filter, backdrop-filter;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
  &:hover {
    border-color: rgb(158 188 247);
    box-shadow: 0 8px 25px #4473ba0d;
  }
  @media (min-width: 768px) {
    & {
      padding: 19px;
    }
  }
  & > p {
    margin-top: 17px;
    margin-bottom: 17px;
    font-size: 11px;
    color: rgb(154 169 187);
  }
`;

export const areaCardHeader = css`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  & > div {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  & strong {
    font-size: 0.875rem;
    line-height: 1.25rem;
  }
`;

export const areaIcon = css`
  display: grid;
  height: 2rem;
  width: 2rem;
  place-items: center;
  border-radius: 9px;
  background-color: rgb(237 243 255);
  color: rgb(84 129 233);
`;

export const statusGrid = css`
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.375rem;
`;

export const statusCell = css`
  display: grid;
  height: 39px;
  place-items: center;
  border-radius: 0.375rem;
  font-size: 10px;
  font-weight: 700;
`;

export const areaActivityGrid = css`
  display: grid;
  grid-template-columns: repeat(2, 34px);
  justify-content: center;
  gap: 6px;
  margin-top: 16px;
`;

export const activityCell = css`
  height: 34px;
  border-radius: 2px;
`;

export const areaCardFooter = css`
  margin-top: 1.25rem;
  display: block;
  border-top-width: 1px;
  border-color: rgb(240 243 247);
  padding-top: 0.875rem;
  font-size: 10px;
  line-height: 1.8;
  color: rgb(164 176 191);
  @media (min-width: 768px) {
    & {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
      white-space: nowrap;
    }
  }
  & b {
    display: block;
    color: rgb(107 145 219);
  }
`;

export const prototypeNotice = css`
  margin-top: 22px;
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  border-radius: 10px;
  border-width: 1px;
  border-color: rgb(223 234 255);
  background-color: rgb(240 246 255);
  padding-left: 19px;
  padding-right: 19px;
  padding-top: 17px;
  padding-bottom: 17px;
  font-size: 0.75rem;
  line-height: 1rem;
  color: rgb(82 118 183);
  & > span {
    font-size: 1.125rem;
    line-height: 1.75rem;
  }
  & p {
    margin-top: 5px;
    font-size: 11px;
    color: rgb(138 159 190);
  }
`;

export const noticeIcon = css`
  flex-shrink: 0;
`;

export const appRoot = css`
  min-height: 100vh;
  background-color: rgb(245 248 253);
  font-family: Pretendard, "Apple SD Gothic Neo", sans-serif;
  color: rgb(29 44 70);
`;
