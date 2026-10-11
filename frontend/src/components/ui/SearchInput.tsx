"use client";

import type { InputHTMLAttributes } from "react";

export type SearchInputProps = InputHTMLAttributes<HTMLInputElement>;

/** Search field with light/dark theme support. */
export default function SearchInput({ className = "", ...rest }: SearchInputProps) {
  return (
    <input
      className={`w-full bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg px-4 py-2 text-xs text-neutral-900 dark:text-neutral-200 placeholder-neutral-400 dark:placeholder-neutral-500 focus:outline-none focus:border-neutral-400 dark:focus:border-neutral-500 transition ${className}`}
      {...rest}
    />
  );
}
