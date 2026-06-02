import type { Kpi } from "@/lib/discover/types";

// Mini sparkline for KPI cards — replaces the progress bar.
// Transcribed verbatim from
// /tmp/cortex-handoff/cortex/project/cortex/dashboard.jsx lines 104–120.
export function MiniSparkline({ trend }: { trend: Kpi["trend"] }) {
  const trends: Record<Kpi["trend"], number[]> = {
    answers: [0.18, 0.22, 0.28, 0.32, 0.38, 0.42, 0.48, 0.55, 0.58, 0.65, 0.72, 0.8],
    views: [0.28, 0.24, 0.34, 0.34, 0.46, 0.42, 0.55, 0.52, 0.66, 0.72, 0.78, 0.86],
    clicks: [0.3, 0.26, 0.34, 0.38, 0.32, 0.46, 0.5, 0.58, 0.54, 0.62, 0.7, 0.78],
    revenue: [0.35, 0.40, 0.42, 0.38, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.88],
  };
  const pts = trends[trend] ?? trends.answers;
  const w = 140,
    h = 28,
    pad = 1.5;
  const xs = pts.map((_, i) => pad + (i / (pts.length - 1)) * (w - pad * 2));
  const ys = pts.map((p) => pad + (1 - p) * (h - pad * 2));
  const d = xs
    .map((x, i) => `${i ? "L" : "M"}${x.toFixed(1)} ${ys[i].toFixed(1)}`)
    .join(" ");
  return (
    <svg
      className="mini-spk"
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <path
        d={d}
        fill="none"
        stroke="#1C726B"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}
