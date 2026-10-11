"use client";

import { Spinner } from "./ui";

export default function LoadingOverlay({ message }: { message: string }) {
  return (
    <div className="fixed inset-0 bg-black/85 backdrop-blur-sm z-50 flex items-center justify-center flex-col space-y-4">
      <Spinner size="lg" />
      <p className="text-sm font-semibold text-neutral-200">{message}</p>
    </div>
  );
}
