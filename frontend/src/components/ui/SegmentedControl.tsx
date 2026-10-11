"use client";

import type { ReactNode } from "react";

export interface SegmentOption<T extends string | number> {
  value: T;
  label: ReactNode;
}

interface SegmentedControlProps<T extends string | number> {
  label?: ReactNode;
  options: SegmentOption<T>[];
  active: T;
  onChange: (value: T) => void;
}

/** Compact pill group (e.g. Show: All / Top 5 / Top 10). */
export default function SegmentedControl<T extends string | number>({
  label,
  options,
  active,
  onChange,
}: SegmentedControlProps<T>) {
  return (
    <div className="flex items-center space-x-1 bg-neutral-100 dark:bg-neutral-900 p-1 rounded-xl border border-neutral-200 dark:border-neutral-800 transition-colors">
      {label && (
        <span className="text-[11px] font-semibold text-neutral-500 dark:text-neutral-400 px-2">{label}</span>
      )}
      {options.map((o) => (
        <button
          key={String(o.value)}
          type="button"
          onClick={() => onChange(o.value)}
          className={
            o.value === active
              ? "px-2.5 py-1 text-xs font-semibold rounded-lg bg-white dark:bg-white text-neutral-900 dark:text-black shadow-sm transition"
              : "px-2.5 py-1 text-xs font-semibold rounded-lg text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white hover:bg-neutral-200 dark:hover:bg-neutral-800 transition"
          }
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
