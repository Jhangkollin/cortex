interface ConstellationSVGProps {
  size?: number;
  brandMono?: string;
  accent?: string;
  mediaLabels?: string[];
  productCount?: number;
}

/**
 * Brand Constellation — redesigned for Cortex design language.
 *
 * Architecture:
 *   - Center: brand anchor disc (teal-700) + monogram + decorative pulse rings
 *   - Inner orbit: product-line nodes (dashed ring, small filled circles)
 *   - Outer orbit: media-publisher nodes (white disc, teal outline, dot, label)
 *   - Connections: radial spokes center → media (low opacity)
 *   - Background: radial teal glow + subtle coordinate grid
 *   - Tick ring: precision markers on outer orbit
 *
 * Uses hardcoded teal values so the SVG renders correctly in the
 * report-viewer context where CSS custom properties may not resolve.
 */
export function ConstellationSVG({
  size = 440,
  brandMono = "A",
  mediaLabels,
  productCount = 5,
}: ConstellationSVGProps) {
  const cx = size / 2;
  const cy = size / 2;

  const TEAL_700 = "#1C726B";
  const TEAL_400 = "#38A69A";
  const TEAL_100 = "#B2DFDB";

  const coreR   = size * 0.115;   // brand disc
  const innerR  = size * 0.215;   // product orbit
  const outerR  = size * 0.395;   // media orbit

  const mediaCount = mediaLabels && mediaLabels.length > 0 ? Math.min(mediaLabels.length, 8) : 6;

  const mediaPts = Array.from({ length: mediaCount }, (_, i) => {
    const a = (i / mediaCount) * Math.PI * 2 - Math.PI / 2;
    return {
      x: cx + Math.cos(a) * outerR,
      y: cy + Math.sin(a) * outerR,
      label: mediaLabels?.[i] ?? "",
    };
  });

  const prodCount = Math.max(3, productCount);
  const productPts = Array.from({ length: prodCount }, (_, i) => {
    const a = ((i + 0.5) / prodCount) * Math.PI * 2 - Math.PI / 2;
    return {
      x: cx + Math.cos(a) * innerR,
      y: cy + Math.sin(a) * innerR,
    };
  });

  // Tick marks on outer ring
  const TICKS = 48;
  const ticks = Array.from({ length: TICKS }, (_, i) => {
    const a  = (i / TICKS) * Math.PI * 2;
    const r0 = outerR - 2;
    const r1 = outerR + (i % 4 === 0 ? 7 : 3);
    return {
      x1: cx + Math.cos(a) * r0,
      y1: cy + Math.sin(a) * r0,
      x2: cx + Math.cos(a) * r1,
      y2: cy + Math.sin(a) * r1,
      major: i % 4 === 0,
    };
  });

  // Faint coordinate grid lines
  const GRID_LINES = 6;
  const gridLines = Array.from({ length: GRID_LINES }, (_, i) => {
    const a = (i / GRID_LINES) * Math.PI;
    return {
      x1: cx + Math.cos(a) * outerR * 1.1,
      y1: cy + Math.sin(a) * outerR * 1.1,
      x2: cx + Math.cos(a + Math.PI) * outerR * 1.1,
      y2: cy + Math.sin(a + Math.PI) * outerR * 1.1,
    };
  });

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      style={{ display: "block" }}
      aria-hidden
    >
      <defs>
        <radialGradient id="cg-glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%"   stopColor={TEAL_700} stopOpacity="0.12" />
          <stop offset="45%"  stopColor={TEAL_700} stopOpacity="0.04" />
          <stop offset="100%" stopColor={TEAL_700} stopOpacity="0"    />
        </radialGradient>
        <radialGradient id="cg-core" cx="50%" cy="50%" r="50%">
          <stop offset="0%"   stopColor={TEAL_400} stopOpacity="0.30" />
          <stop offset="100%" stopColor={TEAL_700} stopOpacity="0"    />
        </radialGradient>
      </defs>

      {/* Background radial glow */}
      <circle cx={cx} cy={cy} r={outerR * 1.2} fill="url(#cg-glow)" />

      {/* Faint coordinate grid */}
      {gridLines.map((l, i) => (
        <line key={`g-${i}`}
          x1={l.x1} y1={l.y1} x2={l.x2} y2={l.y2}
          stroke={TEAL_700} strokeOpacity="0.04" strokeWidth="0.6"
        />
      ))}

      {/* Outer orbit ring */}
      <circle cx={cx} cy={cy} r={outerR}
        fill="none" stroke={TEAL_700} strokeOpacity="0.14" strokeWidth="0.8"
      />

      {/* Tick marks */}
      {ticks.map((t, i) => (
        <line key={`t-${i}`}
          x1={t.x1} y1={t.y1} x2={t.x2} y2={t.y2}
          stroke={TEAL_700}
          strokeOpacity={t.major ? 0.30 : 0.12}
          strokeWidth={t.major ? 1.0 : 0.6}
        />
      ))}

      {/* Inner dashed orbit (product) */}
      <circle cx={cx} cy={cy} r={innerR}
        fill="none" stroke={TEAL_700}
        strokeOpacity="0.20" strokeWidth="0.7" strokeDasharray="3 6"
      />

      {/* Center soft glow halo */}
      <circle cx={cx} cy={cy} r={coreR * 1.8} fill="url(#cg-core)" />

      {/* Spokes: center → media nodes */}
      {mediaPts.map((m, i) => (
        <line key={`sp-${i}`}
          x1={cx} y1={cy} x2={m.x} y2={m.y}
          stroke={TEAL_700} strokeOpacity="0.08" strokeWidth="0.5"
        />
      ))}

      {/* Product → nearest media (dashed) */}
      {productPts.map((p, i) => {
        const m = mediaPts[i % mediaCount];
        if (!m) return null;
        return (
          <line key={`pm-${i}`}
            x1={p.x} y1={p.y} x2={m.x} y2={m.y}
            stroke={TEAL_700} strokeOpacity="0.10"
            strokeWidth="0.5" strokeDasharray="2 5"
          />
        );
      })}

      {/* Product nodes */}
      {productPts.map((p, i) => (
        <g key={`p-${i}`}>
          <circle cx={p.x} cy={p.y} r="6"
            fill={TEAL_700} fillOpacity="0.08"
          />
          <circle cx={p.x} cy={p.y} r="3.5"
            fill={TEAL_700} fillOpacity="0.55"
          />
        </g>
      ))}

      {/* Media nodes */}
      {mediaPts.map((m, i) => (
        <g key={`m-${i}`}>
          <circle cx={m.x} cy={m.y} r="11"
            fill="white" stroke={TEAL_700}
            strokeOpacity="0.55" strokeWidth="1.2"
          />
          <circle cx={m.x} cy={m.y} r="4"
            fill={TEAL_700} fillOpacity="0.65"
          />
          {m.label ? (
            <text
              x={m.x} y={m.y - 18}
              textAnchor="middle"
              fontFamily="'Roboto Mono', monospace"
              fontSize="8.5"
              fill={TEAL_700}
              fillOpacity="0.65"
              letterSpacing="0.05em"
            >
              {m.label.length > 12 ? `${m.label.slice(0, 12)}…` : m.label}
            </text>
          ) : null}
        </g>
      ))}

      {/* Center brand anchor */}
      {/* Outer decorative dashed ring */}
      <circle cx={cx} cy={cy} r={coreR + 10}
        fill="none" stroke={TEAL_400}
        strokeOpacity="0.35" strokeWidth="1.2" strokeDasharray="2 4"
      />
      {/* Soft halo ring */}
      <circle cx={cx} cy={cy} r={coreR + 4}
        fill="none" stroke={TEAL_700} strokeOpacity="0.10" strokeWidth="5"
      />
      {/* Main disc */}
      <circle cx={cx} cy={cy} r={coreR} fill={TEAL_700} />
      {/* Inner highlight */}
      <circle cx={cx} cy={cy - coreR * 0.25} r={coreR * 0.55}
        fill="white" fillOpacity="0.05"
      />
      {/* Monogram */}
      <text
        x={cx} y={cy + 9}
        textAnchor="middle"
        fontFamily="'Noto Sans', system-ui, sans-serif"
        fontSize={coreR * 0.72}
        fontWeight="800"
        fill="white"
      >
        {brandMono}
      </text>

      {/* Four cardinal micro-labels on outer ring */}
      {[
        { a: -Math.PI / 2, label: "N" },
        { a: 0,            label: "E" },
        { a: Math.PI / 2,  label: "S" },
        { a: Math.PI,      label: "W" },
      ].map(({ a, label }) => (
        <text key={label}
          x={cx + Math.cos(a) * (outerR + 16)}
          y={cy + Math.sin(a) * (outerR + 16) + 3}
          textAnchor="middle"
          fontFamily="'Roboto Mono', monospace"
          fontSize="7"
          fill={TEAL_700}
          fillOpacity="0.25"
          letterSpacing="0.1em"
        >
          {label}
        </text>
      ))}

      {/* Corner coordinate readout — decorative precision detail */}
      <text
        x={size - 10} y={size - 14}
        textAnchor="end"
        fontFamily="'Roboto Mono', monospace"
        fontSize="7"
        fill={TEAL_700}
        fillOpacity="0.20"
        letterSpacing="0.08em"
      >
        {`${mediaCount}P · ${prodCount}L`}
      </text>

      {/* Outer boundary circle (very faint) */}
      <circle cx={cx} cy={cy} r={size * 0.48}
        fill="none" stroke={TEAL_100} strokeOpacity="0.15" strokeWidth="0.5"
      />
    </svg>
  );
}
