import type { ButtonHTMLAttributes, ReactNode } from "react";
import type { Interpolation, Theme } from "@emotion/react";
import * as styles from "../../../styles";

type ButtonVariant = "primary" | "secondary" | "text";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  children: ReactNode;
  css?: Interpolation<Theme>;
}

const variantStyles = {
  primary: styles.primaryButton,
  secondary: styles.secondaryButton,
  text: styles.textButton,
};

export function Button({ variant = "secondary", css, children, ...props }: ButtonProps) {
  return (
    <button css={[variantStyles[variant], css]} {...props}>
      {children}
    </button>
  );
}
