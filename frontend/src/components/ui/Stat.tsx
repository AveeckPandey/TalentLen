"use client";

import type { ReactNode } from "react";

interface StatProps {
  label: string;
  value: ReactNode;
  valueClassName?: string;
  className?: string;
}

/** Single summary metric cell for the batch overview grid. */
export default function Stat({
  label,
  value,
  valueClassName = "",
  className = "",
}: StatProps) {
  return (
    <div className={`bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl p-4 text-center transition-colors shadow-sm ${className}`}>
      <p className="text-xs font-medium text-neutral-500 dark:text-neutral-400">{label}</p>
      <p className={`text-2xl font-bold mt-1 text-neutral-900 dark:text-white ${valueClassName}`}>{value}</p>
    </div>
  );
}
