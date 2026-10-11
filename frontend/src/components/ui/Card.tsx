"use client";

import type { HTMLAttributes } from "react";

export type CardProps = HTMLAttributes<HTMLDivElement>;

/** Responsive light/dark panel container. */
export default function Card({ className = "", ...rest }: CardProps) {
  return (
    <div
      className={`bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 text-neutral-900 dark:text-neutral-100 rounded-xl shadow-sm transition-colors duration-200 ${className}`}
      {...rest}
    />
  );
}
