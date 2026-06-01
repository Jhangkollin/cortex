import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * Mlytics pill / badge.
 *
 * Variants per the handoff:
 *   live  — teal, has an animated 6×6 dot that pulses on a 2s loop
 *   beta  — amber
 *   soon  — neutral grey
 *   ent   — purple (Enterprise tier)
 *   real  — amber-on-amber-bg (REAL DATA marker)
 *
 * 11px / 700 weight / uppercase / 0.04em tracking.
 */
const badgeVariants = cva(
  [
    "inline-flex items-center gap-1.5",
    "rounded-full border bg-white",
    "px-2.5 py-[2px]",
    "text-[11px] font-bold uppercase tracking-[0.04em] leading-tight",
  ].join(" "),
  {
    variants: {
      variant: {
        live: "text-brand-700 border-brand-200 bg-[#F2F8F7]",
        beta: "text-amber-600 border-amber-200 bg-amber-50",
        soon: "text-ink-500 border-ink-200 bg-ink-50",
        ent: "text-purple-fg border-purple-bd bg-purple-bg",
        real: "text-amber-600 border-amber-200 bg-amber-50",
      },
    },
    defaultVariants: {
      variant: "live",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({
  className,
  variant = "live",
  children,
  ...props
}: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props}>
      {variant === "live" ? (
        <span
          aria-hidden
          className="h-1.5 w-1.5 rounded-full bg-success"
          style={{ animation: "mly-pulse 2s infinite" }}
        />
      ) : null}
      {children}
    </span>
  );
}

export { badgeVariants };
