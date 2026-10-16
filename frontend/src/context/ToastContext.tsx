"use client";

import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import ToastContainer, { ToastItem } from "@/components/ui/Toast";

interface ToastContextType {
  toasts: ToastItem[];
  showToast: (toast: Omit<ToastItem, "id">) => string;
  showError: (title: string, message?: string, action?: { label: string; onClick: () => void }) => string;
  showSuccess: (title: string, message?: string) => string;
  showInfo: (title: string, message?: string) => string;
  showWarning: (title: string, message?: string) => string;
  dismissToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

// Global bridge for non-react calls (e.g. razorpay callbacks)
type ToastListener = (toast: Omit<ToastItem, "id">) => string;
let globalToastEmitter: ToastListener | null = null;

export const toast = {
  error: (title: string, message?: string, action?: { label: string; onClick: () => void }) => {
    if (globalToastEmitter) {
      return globalToastEmitter({ type: "error", title, message, action, duration: 8000 });
    }
    console.error(`[Toast Error] ${title}: ${message}`);
  },
  success: (title: string, message?: string) => {
    if (globalToastEmitter) {
      return globalToastEmitter({ type: "success", title, message, duration: 5000 });
    }
    console.log(`[Toast Success] ${title}: ${message}`);
  },
  info: (title: string, message?: string) => {
    if (globalToastEmitter) {
      return globalToastEmitter({ type: "info", title, message, duration: 5000 });
    }
    console.info(`[Toast Info] ${title}: ${message}`);
  },
  warning: (title: string, message?: string) => {
    if (globalToastEmitter) {
      return globalToastEmitter({ type: "warning", title, message, duration: 6000 });
    }
    console.warn(`[Toast Warning] ${title}: ${message}`);
  },
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    (item: Omit<ToastItem, "id">) => {
      const id = "toast_" + Math.random().toString(36).slice(2, 9);
      const newToast: ToastItem = {
        ...item,
        id,
      };

      setToasts((prev) => [...prev.slice(-4), newToast]); // Keep at most 5 toasts visible

      const duration = item.duration !== undefined ? item.duration : (item.type === "error" ? 8000 : 5000);
      if (duration > 0) {
        setTimeout(() => {
          dismissToast(id);
        }, duration);
      }

      return id;
    },
    [dismissToast]
  );

  useEffect(() => {
    globalToastEmitter = showToast;
    // Silent warm-up ping to wake up backend immediately on page visit
    if (typeof window !== "undefined") {
      try {
        import("@/lib/api").then(({ apiUrl }) => {
          fetch(apiUrl("/health"), { method: "GET" }).catch(() => {});
        });
      } catch {
        /* best-effort */
      }
    }
    return () => {
      globalToastEmitter = null;
    };
  }, [showToast]);

  const showError = useCallback(
    (title: string, message?: string, action?: { label: string; onClick: () => void }) => {
      return showToast({ type: "error", title, message, action, duration: action ? 10000 : 7000 });
    },
    [showToast]
  );

  const showSuccess = useCallback(
    (title: string, message?: string) => {
      return showToast({ type: "success", title, message, duration: 5000 });
    },
    [showToast]
  );

  const showInfo = useCallback(
    (title: string, message?: string) => {
      return showToast({ type: "info", title, message, duration: 5000 });
    },
    [showToast]
  );

  const showWarning = useCallback(
    (title: string, message?: string) => {
      return showToast({ type: "warning", title, message, duration: 6000 });
    },
    [showToast]
  );

  return (
    <ToastContext.Provider
      value={{
        toasts,
        showToast,
        showError,
        showSuccess,
        showInfo,
        showWarning,
        dismissToast,
      }}
    >
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    // Return fallback in case used outside provider
    return {
      toasts: [],
      showToast: (t: Omit<ToastItem, "id">) => {
        toast.info(t.title, t.message);
        return "";
      },
      showError: (title: string, message?: string, action?: { label: string; onClick: () => void }) => {
        toast.error(title, message, action);
        return "";
      },
      showSuccess: (title: string, message?: string) => {
        toast.success(title, message);
        return "";
      },
      showInfo: (title: string, message?: string) => {
        toast.info(title, message);
        return "";
      },
      showWarning: (title: string, message?: string) => {
        toast.warning(title, message);
        return "";
      },
      dismissToast: () => {},
    };
  }
  return context;
}
