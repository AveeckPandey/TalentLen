"use client";

import type { ReactNode } from "react";

interface SliderProps {
  label: ReactNode;
  display: string;
  min: number;
  max: number;
  step: number;
  value: number;
  onChange: (value: number) => void;
  marks?: (string | number)[];
}

/** Labeled range slider with value badge and optional scale marks. */
export default function Slider({
  label,
  display,
  min,
  max,
  step,
  value,
  onChange,
  marks,
}: SliderProps) {
  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="font-bold text-neutral-200">{label}</span>
        <span className="font-extrabold text-white px-2 py-0.5 rounded bg-neutral-800 border border-neutral-700 text-xs">
          {display}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-white cursor-pointer"
      />
      {marks && marks.length > 0 && (
        <div className="flex justify-between text-[9px] text-neutral-400 mt-0.5 font-medium">
          {marks.map((m) => (
            <span key={String(m)}>{m}</span>
          ))}
        </div>
      )}
    </div>
  );
}
