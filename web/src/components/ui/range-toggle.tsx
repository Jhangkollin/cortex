"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * Range toggle — segmented 7d / 30d / 90d control used on Discover and Nexus.
 *
 * Pill background ink-100; the active option lifts to white + elev-1 to
 * read as "selected". Per spec: pill-shaped, no rim, 120ms ease transitions.
 *
 * Controlled component — pass `value` and `onChange`. Generic over the option
 * union so callers can name their own ranges; defaults to the typical 3-step.
 */
export interface RangeToggleProps<T extends string> {
  options: readonly T[];
  value: T;
  onChange: (next: T) => void;
  className?: string;
  ariaLabel?: string;
}

export function RangeToggle<T extends string>({
  options,
  value,
  onChange,
  className,
  ariaLabel = "Time range",
}: RangeToggleProps<T>) {
  return (
    <div
      role="tablist"
      aria-label={ariaLabel}
      className={cn(
        "inline-flex items-center gap-0.5 rounded-full bg-ink-100 p-[3px]",
        className,
      )}
    >
      {options.map((opt) => {
        const isActive = opt === value;
        return (
          <button
            key={opt}
            role="tab"
            aria-selected={isActive}
            type="button"
            onClick={() => onChange(opt)}
            className={cn(
              "rounded-full px-3.5 py-1.5 text-xs font-medium",
              "transition-[background-color,color,box-shadow] duration-state ease-std",
              isActive
                ? "bg-white text-ink-800 shadow-elev-1"
                : "bg-transparent text-ink-500 hover:text-ink-800",
            )}
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
}
