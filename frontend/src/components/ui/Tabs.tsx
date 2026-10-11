"use client";

import type { ReactNode } from "react";

export interface TabOption<T extends string> {
  value: T;
  label: ReactNode;
}

interface TabsProps<T extends string> {
  options: TabOption<T>[];
  active: T;
  onChange: (value: T) => void;
}

/** Primary tab switcher (e.g. Ranked Eligible / Disqualified). */
export default function Tabs<T extends string>({ options, active, onChange }: TabsProps<T>) {
  return (
    <div className="flex items-center space-x-2">
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          onClick={() => onChange(o.value)}
          className={
            o.value === active
              ? "px-4 py-2 text-sm font-semibold rounded-lg bg-neutral-900 text-white dark:bg-white dark:text-black transition shadow-sm"
              : "px-4 py-2 text-sm font-semibold rounded-lg bg-white text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 border border-neutral-200 dark:bg-neutral-900 dark:text-neutral-400 dark:hover:text-white dark:hover:bg-neutral-800 dark:border-neutral-800 transition"
          }
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
