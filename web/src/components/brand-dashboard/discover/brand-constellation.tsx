"use client";

import type { ReactElement } from "react";

export interface BrandConstellationProps {
  size?: number;
  mono?: string;
  /** Accent color for product/media dots — defaults to var(--gold). */
  accent?: string;
  /**
   * When true, render connector lines between media and product points
   * (celebration variant). Defaults to false (hero variant).
   */
  showConnectorLines?: boolean;
  /** Override the center disc + monogram font size (defaults: size * 0.18). */
  monogramFontSize?: number;
}

export function BrandConstellation({
  size = 220,
  mono = "B",
  accent = "var(--gold)",
  showConnectorLines = false,
  monogramFontSize,
}: BrandConstellationProps): ReactElement {
  const cx = size / 2,
    cy = size / 2;
  const innerR = size * 0.2,
    midR = size * 0.32,
    outerR = size * 0.44;
  const mediaCount = 6,
    productCount = 7;
  const fontSize = monogramFontSize ?? size * 0.18;

  const mediaPts = Array.from({ length: mediaCount }, (_, i) => {
    const a = ((i / mediaCount) * Math.PI * 2) - Math.PI / 2;
    return { x: cx + Math.cos(a) * outerR, y: cy + Math.sin(a) * outerR };
  });
  const productPts = Array.from({ length: productCount }, (_, i) => {
    const a = ((i / productCount) * Math.PI * 2) - Math.PI / 2 + 0.35;
    return { x: cx + Math.cos(a) * midR, y: cy + Math.sin(a) * midR };
  });

  // Unique gradient id per instance avoids SVG id collisions when both
  // celebration and hero render on the same page simultaneously.
  const gradId = showConnectorLines ? "brConGlowCel" : "brConGlowHero";

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      style={{ display: "block" }}
    >
      <defs>
        <radialGradient id={gradId} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={accent} stopOpacity="0.18" />
          <stop offset="100%" stopColor={accent} stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx={cx} cy={cy} r={size * 0.48} fill={`url(#${gradId})`} />

      {/* Orbit rings */}
      {([innerR, midR, outerR] as const).map((r, i) => (
        <circle
          key={i}
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke="rgba(110,96,69,0.30)"
          strokeDasharray={i === 1 ? "2 4" : ""}
        />
      ))}

      {/* Product points — spoke lines from center + optional cross-lines to media */}
      {productPts.map((p, i) => (
        <g key={i}>
          <line
            x1={cx}
            y1={cy}
            x2={p.x}
            y2={p.y}
            stroke={accent}
            strokeOpacity="0.18"
            strokeWidth="0.6"
          />
          {showConnectorLines && i < mediaCount && (
            <line
              x1={p.x}
              y1={p.y}
              x2={mediaPts[i].x}
              y2={mediaPts[i].y}
              stroke="rgba(28,114,107,0.18)"
              strokeWidth="0.5"
            />
          )}
          <circle cx={p.x} cy={p.y} r="3.5" fill={accent} opacity={0.7} />
        </g>
      ))}

      {/* Media points — ring + filled dot */}
      {mediaPts.map((m, i) => (
        <g key={`m-${i}`}>
          <circle
            cx={m.x}
            cy={m.y}
            r="7.5"
            fill="none"
            stroke={accent}
            strokeWidth="1.2"
            opacity={0.8}
          />
          <circle cx={m.x} cy={m.y} r="3" fill={accent} />
        </g>
      ))}

      {/* Center disc — brand stamp: teal disc + white monogram */}
      <circle cx={cx} cy={cy} r={innerR * 0.55} fill="var(--brand-teal)" />
      <text
        x={cx}
        y={cy + fontSize * 0.3}
        textAnchor="middle"
        fontFamily="var(--font-serif, serif)"
        fontSize={fontSize}
        fontWeight="700"
        fill="#fff"
      >
        {mono}
      </text>
    </svg>
  );
}
