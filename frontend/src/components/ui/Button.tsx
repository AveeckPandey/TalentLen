"use client";

import type { ButtonHTMLAttributes } from "react";

export type ButtonVariant =
  | "primary"
  | "secondary"
  | "soft"
  | "dark"
  | "link"
  | "navLink"
  | "pill";
export type ButtonSize = "xs" | "sm" | "md" | "lg" | "none";

const VARIANTS: Record<ButtonVariant, string> = {
  primary: "bg-white text-black hover:bg-neutral-200 border border-white",
  secondary: "bg-neutral-800 text-neutral-200 hover:bg-neutral-700 border border-neutral-700",
  soft: "bg-neutral-800 text-neutral-300 hover:bg-neutral-700 border border-neutral-700",
  dark: "bg-neutral-900 text-neutral-200 hover:bg-neutral-800 border border-neutral-700",
  link: "hover:text-white underline border-transparent",
  navLink: "text-neutral-600 hover:text-black border-transparent",
  pill: "bg-neutral-100 text-neutral-900 hover:bg-neutral-200 border border-transparent",
};

const SIZES: Record<ButtonSize, string> = {
  xs: "px-2 py-0.5 text-xs",
  sm: "px-2.5 py-1 text-xs",
  md: "px-3 py-1.5 text-xs",
  lg: "px-4 py-2.5 text-sm",
  none: "",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

/** Shared button. Weight/rounding are caller-provided via className to avoid Tailwind conflicts. */
export default function Button({
  variant = "secondary",
  size = "md",
  className = "",
  type = "button",
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`inline-flex items-center justify-center gap-1.5 transition disabled:opacity-50 disabled:cursor-not-allowed ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...rest}
    />
  );
}
