interface ConstellationSVGProps {
  size?: number;
  brandMono?: string;
  accent?: string;
  /**
   * Real media-outlet labels from the report. When supplied, node text uses
   * these (truncated). When omitted, nodes render with no text — the SVG is
   * decorative and must never display fabricated media names.
   */
  mediaLabels?: string[];
  /** Number of product-orbit nodes (defaults to a decorative 7). */
  productCount?: number;
}

/**
 * Brand constellation — Light Edition (per direction-c.jsx in the design
 * bundle). Center disc keeps the brand-teal anchor with a white monogram
 * (intentionally preserved across the dark→light flip — it IS the brand
 * mark). Orbit rings flip from white-on-dark dashes to warm-gray paper-ink
 * dashes; connecting lines warm to a low-opacity teal; media nodes become
 * white-filled with a teal stroke + dot so they read as "satellites" on
 * cream paper.
 *
 * `mediaLabels` is still honoured — when supplied, real outlet names are
 * stamped above each media node (truncated to 8 chars). With no labels the
 * nodes stay anonymous so the graphic never asserts fabricated outlets.
 */
export function ConstellationSVG({
  size = 380,
  brandMono = "A",
  accent = "var(--brand-teal)",
  mediaLabels,
  productCount = 7,
}: ConstellationSVGProps) {
  const cx = size / 2;
  const cy = size / 2;
  const innerR = size * 0.2;
  const midR = size * 0.32;
  const outerR = size * 0.44;
  // Node count tracks real labels when provided; otherwise a decorative 6.
  const mediaCount = mediaLabels && mediaLabels.length > 0 ? mediaLabels.length : 6;

  const mediaPts = Array.from({ length: mediaCount }, (_, i) => {
    const a = (i / mediaCount) * Math.PI * 2 - Math.PI / 2;
    return {
      x: cx + Math.cos(a) * outerR,
      y: cy + Math.sin(a) * outerR,
      label: mediaLabels?.[i] ?? "",
    };
  });

  const productPts = Array.from({ length: productCount }, (_, i) => {
    const a = (i / productCount) * Math.PI * 2 - Math.PI / 2 + 0.35;
    return {
      x: cx + Math.cos(a) * midR,
      y: cy + Math.sin(a) * midR,
    };
  });

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      style={{ display: "block" }}
    >
      <defs>
        <radialGradient id="bgGlowLite" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={accent} stopOpacity="0.10" />
          <stop offset="60%" stopColor={accent} stopOpacity="0.03" />
          <stop offset="100%" stopColor={accent} stopOpacity="0" />
        </radialGradient>
      </defs>

      <circle cx={cx} cy={cy} r={size * 0.48} fill="url(#bgGlowLite)" />

      {/* orbit rings — warm-gray dashed on cream paper */}
      {[innerR, midR, outerR].map((r, i) => (
        <circle
          key={i}
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke={`rgba(var(--paper-ink-rgb), 0.18)`}
          strokeDasharray={i === 1 ? "2 4" : undefined}
        />
      ))}

      {/* brand → product lines (low-opacity teal) */}
      {productPts.map((p, i) => (
        <line
          key={`pl-${i}`}
          x1={cx}
          y1={cy}
          x2={p.x}
          y2={p.y}
          stroke={accent}
          strokeOpacity="0.30"
          strokeWidth="0.7"
        />
      ))}

      {/* product → nearest media (low-opacity warm-gray) */}
      {productPts.map((p, i) => {
        const m = mediaPts[i % mediaCount];
        if (!m) return null;
        return (
          <line
            key={`pm-${i}`}
            x1={p.x}
            y1={p.y}
            x2={m.x}
            y2={m.y}
            stroke={`rgba(var(--paper-ink-rgb), 0.18)`}
            strokeWidth="0.5"
          />
        );
      })}

      {/* product nodes — small teal dots */}
      {productPts.map((p, i) => (
        <circle key={`p-${i}`} cx={p.x} cy={p.y} r="3.5" fill={accent} opacity={0.75} />
      ))}

      {/* media nodes — white discs with teal outline + dot, optional label */}
      {mediaPts.map((m, i) => (
        <g key={`m-${i}`}>
          <circle
            cx={m.x}
            cy={m.y}
            r="7.5"
            fill="var(--card-white)"
            stroke={accent}
            strokeWidth="1.4"
          />
          <circle cx={m.x} cy={m.y} r="3" fill={accent} />
          {m.label ? (
            <text
              x={m.x}
              y={m.y - 14}
              textAnchor="middle"
              fontFamily="var(--font-mono)"
              fontSize="9"
              fill="var(--paper-ink-3)"
              letterSpacing="0.1em"
            >
              {m.label.length > 8 ? `${m.label.slice(0, 8)}…` : m.label}
            </text>
          ) : null}
        </g>
      ))}

      {/* centre brand mark — dark teal disc + white monogram. Intentionally
          preserved across the dark→light flip: this IS the brand anchor and
          must read as such on cream paper. A gold dashed ring hints at the
          "ceremony" accent without colouring the disc itself. */}
      <g>
        <circle
          cx={cx}
          cy={cy}
          r={innerR * 0.62}
          fill="none"
          stroke="var(--mly-teal-400)"
          strokeWidth="1.5"
          strokeDasharray="2 3"
          opacity={0.6}
        />
        <circle cx={cx} cy={cy} r={innerR * 0.55} fill="var(--brand-teal)" />
        <text
          x={cx}
          y={cy + 9}
          textAnchor="middle"
          fontFamily="var(--font-serif)"
          fontSize="28"
          fontWeight="700"
          fill="#fff"
        >
          {brandMono}
        </text>
      </g>
    </svg>
  );
}
