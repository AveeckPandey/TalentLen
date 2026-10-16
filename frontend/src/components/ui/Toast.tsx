"use client";

import React from "react";

export interface ToastItem {
  id: string;
  type: "error" | "success" | "info" | "warning";
  title: string;
  message?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  duration?: number;
}

export interface ToastProps {
  toasts: ToastItem[];
  onDismiss: (id: string) => void;
}

export default function ToastContainer({ toasts, onDismiss }: ToastProps) {
  if (!toasts || toasts.length === 0) return null;

  return (
    <div
      aria-live="assertive"
      className="fixed top-4 right-4 z-[9999] flex flex-col gap-2.5 max-w-sm sm:max-w-md w-full pointer-events-none px-3 sm:px-0"
    >
      {toasts.map((t) => {
        const isError = t.type === "error";
        const isSuccess = t.type === "success";
        const isWarning = t.type === "warning";

        const borderClass = isError
          ? "border-red-500/40 dark:border-red-500/30 bg-red-50/95 dark:bg-neutral-900/95 shadow-red-500/10"
          : isSuccess
          ? "border-emerald-500/40 dark:border-emerald-500/30 bg-emerald-50/95 dark:bg-neutral-900/95 shadow-emerald-500/10"
          : isWarning
          ? "border-amber-500/40 dark:border-amber-500/30 bg-amber-50/95 dark:bg-neutral-900/95 shadow-amber-500/10"
          : "border-blue-500/40 dark:border-blue-500/30 bg-blue-50/95 dark:bg-neutral-900/95 shadow-blue-500/10";

        const iconColor = isError
          ? "text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-950/60"
          : isSuccess
          ? "text-emerald-600 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-950/60"
          : isWarning
          ? "text-amber-600 dark:text-amber-400 bg-amber-100 dark:bg-amber-950/60"
          : "text-[#0066FF] dark:text-blue-400 bg-blue-100 dark:bg-blue-950/60";

        return (
          <div
            key={t.id}
            role="alert"
            className={`pointer-events-auto flex items-start gap-3 p-3.5 sm:p-4 rounded-xl border shadow-lg backdrop-blur-md transition-all duration-200 animate-in fade-in slide-in-from-top-2 ${borderClass}`}
          >
            {/* Icon */}
            <div className={`p-1.5 rounded-lg shrink-0 mt-0.5 ${iconColor}`}>
              {isError && (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              )}
              {isSuccess && (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              )}
              {isWarning && (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              )}
              {!isError && !isSuccess && !isWarning && (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0 pr-1">
              <h4 className="text-xs sm:text-sm font-semibold text-neutral-900 dark:text-neutral-100 leading-tight">
                {t.title}
              </h4>
              {t.message && (
                <p className="mt-1 text-[11px] sm:text-xs text-neutral-600 dark:text-neutral-300 leading-relaxed break-words whitespace-pre-wrap">
                  {t.message}
                </p>
              )}
              {t.action && (
                <div className="mt-2.5">
                  <button
                    type="button"
                    onClick={() => {
                      t.action?.onClick();
                      onDismiss(t.id);
                    }}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-[#0066FF] hover:bg-blue-600 shadow-xs transition"
                  >
                    <span>{t.action.label}</span>
                    <span aria-hidden="true">&rarr;</span>
                  </button>
                </div>
              )}
            </div>

            {/* Dismiss Button */}
            <button
              type="button"
              onClick={() => onDismiss(t.id)}
              className="text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200 p-1 -mr-1 -mt-1 rounded-lg transition"
              aria-label="Close notification"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        );
      })}
    </div>
  );
}
