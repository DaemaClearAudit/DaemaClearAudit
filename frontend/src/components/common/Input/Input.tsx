import type { InputHTMLAttributes } from "react";
import type { Interpolation, Theme } from "@emotion/react";
import * as styles from "../../../styles";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  css?: Interpolation<Theme>;
}

export function Input({ css, ...props }: InputProps) {
  return <input css={[styles.textInput, css]} {...props} />;
}
