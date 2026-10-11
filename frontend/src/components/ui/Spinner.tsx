"use client";

type SpinnerSize = "sm" | "md" | "lg";

const SIZES: Record<SpinnerSize, string> = {
  sm: "w-5 h-5 border-2",
  md: "w-8 h-8 border-4",
  lg: "w-12 h-12 border-4",
};

interface SpinnerProps {
  size?: SpinnerSize;
  className?: string;
}

export default function Spinner({ size = "md", className = "" }: SpinnerProps) {
  return (
    <div
      role="status"
      aria-label="Loading"
      className={`${SIZES[size]} border-white border-t-transparent rounded-full animate-spin ${className}`}
    />
  );
}
