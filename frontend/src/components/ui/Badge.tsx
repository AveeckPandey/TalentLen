"use client";

import type { HTMLAttributes } from "react";

export type BadgeVariant = "neutral" | "bright" | "muted" | "faint";
export type BadgeSize = "xs" | "sm";

const VARIANTS: Record<BadgeVariant, string> = {
  neutral: "bg-neutral-800 text-neutral-300 border-neutral-700",
  bright: "bg-neutral-800 text-neutral-200 border-neutral-700",
  muted: "bg-black text-neutral-300 border-neutral-800",
  faint: "bg-neutral-800 text-neutral-400 border-neutral-700",
};

const SIZES: Record<BadgeSize, string> = {
  xs: "px-2 py-0.5 text-[11px]",
  sm: "px-2.5 py-1 text-xs",
};

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  pill?: boolean;
}

/** Small status/skill chip. Weight is caller-provided via className. */
export default function Badge({
  variant = "neutral",
  size = "xs",
  pill = false,
  className = "",
  ...rest
}: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 border ${pill ? "rounded-full" : "rounded"} ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...rest}
    />
  );
}
