import { css } from "@emotion/react";

export const globalStyles = css`
  *,
  ::before,
  ::after {
    box-sizing: border-box;
    border-width: 0;
    border-style: solid;
    border-color: #e5e7eb;
  }
  html {
    font-family: Pretendard, "Apple SD Gothic Neo", sans-serif;
    line-height: 1.5;
    -webkit-text-size-adjust: 100%;
  }
  body {
    margin: 0;
    line-height: inherit;
  }
  h1,
  h2,
  h3,
  p {
    margin: 0;
  }
  h1,
  h2,
  h3 {
    font-size: inherit;
    font-weight: inherit;
  }
  button,
  input,
  select {
    font: inherit;
    color: inherit;
    margin: 0;
    padding: 0;
  }
  button,
  select {
    text-transform: none;
  }
  button {
    cursor: pointer;
    background: transparent;
  }
  button:disabled {
    cursor: default;
  }
  svg {
    display: block;
    vertical-align: middle;
  }
`;
