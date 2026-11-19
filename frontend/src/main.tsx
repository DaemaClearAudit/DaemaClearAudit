import React from "react";
import { createRoot } from "react-dom/client";
import { Global } from "@emotion/react";
import { App } from "./App";
import { globalStyles } from "./styles/global";
import * as styles from "./styles";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Global styles={globalStyles} />
    <div css={styles.appRoot}>
      <App />
    </div>
  </React.StrictMode>,
);
