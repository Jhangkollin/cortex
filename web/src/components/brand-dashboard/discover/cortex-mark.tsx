"use client";

/**
 * CortexMark — inline-SVG brand mark for the Ask Cortex affordance.
 *
 * Mlytics-style rounded teal-gradient square + 4-point sparkle (Cortex
 * AI glyph) + lime accent dot (Mlytics "live" cue). Small enough to fit a
 * 36px FAB; reads as a brand mark rather than a generic Material icon.
 *
 * The defs ID is generated per-instance to avoid linearGradient ID
 * collisions when multiple marks render on the same page.
 */

import { useId } from "react";

export interface CortexMarkProps {
  size?: number;
  className?: string;
}

export function CortexMark({ size = 36, className }: CortexMarkProps) {
  const gid = useId();
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      aria-hidden
      className={className ? `cortex-mark ${className}` : "cortex-mark"}
    >
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#1C726B" />
          <stop offset="100%" stopColor="#0E2D2C" />
        </linearGradient>
      </defs>
      <rect x="1" y="1" width="22" height="22" rx="6" fill={`url(#${gid})`} />
      <path
        d="M 12 5 L 13.4 10.6 L 19 12 L 13.4 13.4 L 12 19 L 10.6 13.4 L 5 12 L 10.6 10.6 Z"
        fill="#FFFFFF"
        opacity="0.95"
      />
      <circle cx="17.8" cy="6.2" r="1.6" fill="#7CB342" />
    </svg>
  );
}
