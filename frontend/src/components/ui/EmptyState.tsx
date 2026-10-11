"use client";

import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  hint?: ReactNode;
  action?: ReactNode;
}

/** Dashed placeholder shown when there is nothing to display yet. */
export default function EmptyState({ title, hint, action }: EmptyStateProps) {
  return (
    <div className="max-w-2xl mx-auto bg-white/80 dark:bg-neutral-900/50 border border-dashed border-neutral-300 dark:border-neutral-800 rounded-2xl p-10 text-center transition-colors">
      <p className="text-sm font-semibold text-neutral-800 dark:text-neutral-300">{title}</p>
      {hint && <p className="text-xs text-neutral-500 dark:text-neutral-500 mt-1">{hint}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
