"use client";

import { useEffect, type ReactNode } from "react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  /** Width cap for the panel, e.g. "max-w-sm" or "max-w-5xl". */
  panelClassName?: string;
  /** Overlay tint, e.g. "bg-black/80" or "bg-black/90". */
  overlayClassName?: string;
  zClassName?: string;
}

/** Overlay + panel shell with Escape-to-close. Callers render header/body inside. */
export default function Modal({
  open,
  onClose,
  children,
  panelClassName = "max-w-lg",
  overlayClassName = "bg-black/80",
  zClassName = "z-50",
}: ModalProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className={`fixed inset-0 ${overlayClassName} backdrop-blur-sm ${zClassName} flex items-center justify-center p-4`}
      onClick={onClose}
    >
      <div className={`w-full ${panelClassName}`} onClick={(e) => e.stopPropagation()}>
        {children}
      </div>
    </div>
  );
}
