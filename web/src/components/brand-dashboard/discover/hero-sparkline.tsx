"use client";

import { useId } from "react";

/**
 * Hero KPI sparkline. SVG path math mirrors `dashboard.jsx` 65–84.
 *
 * The `<linearGradient>` id is generated per instance via `useId()` so the
 * gradient remains unique if the component is rendered more than once on the
 * page (HTML validity + a11y tooling correctness). Matches the per-instance
 * defs-id convention `cortex-mark.tsx` established.
 */
export function HeroSparkline() {
  const gradId = `hero-sparkline-${useId()}`;
  const pts = [0.2, 0.28, 0.24, 0.35, 0.42, 0.36, 0.48, 0.55, 0.5, 0.62, 0.66, 0.74];
  const w = 480,
    h = 180,
    pad = 4;
  const xs = pts.map((_, i) => pad + (i / (pts.length - 1)) * (w - pad * 2));
  const ys = pts.map((p) => pad + (1 - p) * (h - pad * 2));
  const d = xs
    .map((x, i) => `${i ? "L" : "M"}${x.toFixed(1)} ${ys[i].toFixed(1)}`)
    .join(" ");
  const a = `${d} L${xs[xs.length - 1].toFixed(1)} ${h - pad} L${xs[0].toFixed(1)} ${h - pad} Z`;
  return (
    <svg className="spk" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id={gradId} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#1C726B" stopOpacity="0.18" />
          <stop offset="100%" stopColor="#1C726B" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={a} fill={`url(#${gradId})`} />
      <path d={d} fill="none" stroke="#1C726B" strokeWidth="2" />
    </svg>
  );
}
