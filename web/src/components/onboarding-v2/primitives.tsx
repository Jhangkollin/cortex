"use client";

/**
 * Shared UI primitives for /onboarding/v2 — kept private to this module so the
 * one-off variants (amber CTAs, onDark surfaces, the `lg` button size used by
 * the launch hero) don't bleed into the app-wide ui/button.tsx. If a piece of
 * this becomes broadly useful, promote it out — until then, this is a sealed
 * prototype.
 *
 * The zh-Hant sibling at ../onboarding-v2-zh/primitives.tsx is byte-for-byte
 * identical except for translated TopBar copy and a flipped LangSwitch target.
 * Keep them in sync when adding shared primitives.
 */

import Image from "next/image";
import Link from "next/link";
import type { Route } from "next";
import { type CSSProperties, type ReactNode, useEffect, useState } from "react";

import { INTENT_COLOR, type RailIndex } from "./data";

export function Icon({
  name,
  size = 18,
  color,
  style,
}: {
  name: string;
  size?: number;
  color?: string;
  style?: CSSProperties;
}) {
  return (
    <span
      className="material-icons-outlined"
      aria-hidden
      style={{ fontSize: size, color, ...style }}
    >
      {name}
    </span>
  );
}

type Variant = "primary" | "dark" | "soft" | "ghost" | "amber" | "onDark" | "gold";
type Size = "lg" | "md" | "sm" | "xs";

const VARIANT_PALETTE: Record<
  Variant,
  { bg: string; fg: string; border: string; hoverBg: string }
> = {
  primary: { bg: "var(--mly-teal-600)", fg: "#fff", border: "var(--mly-teal-600)", hoverBg: "var(--mly-teal-700)" },
  dark: { bg: "var(--mly-ink-900)", fg: "#fff", border: "var(--mly-ink-900)", hoverBg: "var(--mly-ink-800)" },
  soft: { bg: "#fff", fg: "var(--mly-ink-800)", border: "var(--mly-ink-200)", hoverBg: "var(--mly-ink-050)" },
  ghost: { bg: "transparent", fg: "var(--mly-teal-700)", border: "transparent", hoverBg: "rgba(20,73,72,0.06)" },
  amber: { bg: "var(--cortex-amber-500)", fg: "var(--mly-ink-900)", border: "var(--cortex-amber-500)", hoverBg: "var(--cortex-amber-600)" },
  onDark: { bg: "rgba(255,255,255,0.10)", fg: "#fff", border: "rgba(255,255,255,0.22)", hoverBg: "rgba(255,255,255,0.18)" },
  // Light Edition launch CTAs — solid gold over paper. The drop-shadow glow
  // that previously made these one-off `<button>` elements (see step-launch,
  // launch-overlay, step-complete) is now opt-in via the `glow` prop below.
  gold: { bg: "var(--gold)", fg: "#fff", border: "var(--gold)", hoverBg: "var(--gold-deep)" },
};

const SIZE_DIMS: Record<Size, { h: number; px: number; fs: number }> = {
  lg: { h: 52, px: 22, fs: 15 },
  md: { h: 40, px: 18, fs: 14 },
  sm: { h: 32, px: 14, fs: 13 },
  xs: { h: 28, px: 10, fs: 12 },
};

export function OnbButton({
  variant = "primary",
  size = "md",
  icon,
  iconRight,
  children,
  onClick,
  disabled,
  style,
  type = "button",
  glow,
}: {
  variant?: Variant;
  size?: Size;
  icon?: string;
  iconRight?: string;
  children?: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  style?: CSSProperties;
  type?: "button" | "submit";
  /**
   * Optional drop-shadow applied as `boxShadow`. Used by the Light Edition
   * launch CTAs (gold variant) to add a soft gold haze; default is no shadow
   * so existing call-sites are unaffected. The caller-supplied `style` prop
   * still wins if it also sets boxShadow.
   */
  glow?: string;
}) {
  const v = VARIANT_PALETTE[variant];
  const s = SIZE_DIMS[size];
  const [hover, setHover] = useState(false);
  return (
    <button
      type={type}
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      disabled={disabled}
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 8,
        height: s.h,
        padding: `0 ${s.px}px`,
        fontSize: s.fs,
        fontWeight: 600,
        background: hover && !disabled ? v.hoverBg : v.bg,
        color: v.fg,
        border: `1px solid ${v.border}`,
        borderRadius: 4,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.45 : 1,
        transition: "all 120ms cubic-bezier(0.4,0,0.2,1)",
        whiteSpace: "nowrap",
        fontFamily: "inherit",
        boxShadow: glow,
        ...style,
      }}
    >
      {icon ? <Icon name={icon} size={s.fs + 3} /> : null}
      {children}
      {iconRight ? <Icon name={iconRight} size={s.fs + 3} /> : null}
    </button>
  );
}

export function Card({ children, style }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <div
      style={{
        background: "#fff",
        border: "1px solid var(--mly-ink-150)",
        borderRadius: 10,
        boxShadow: "0 1px 2px rgba(0,0,0,0.04), 0 1px 1px rgba(0,0,0,0.03)",
        ...style,
      }}
    >
      {children}
    </div>
  );
}

type BadgeColor = "ink" | "teal" | "amber" | "real" | "success" | "danger" | "onDark";

const BADGE_PALETTE: Record<BadgeColor, { bg: string; fg: string }> = {
  ink: { bg: "var(--mly-ink-100)", fg: "var(--mly-ink-700)" },
  teal: { bg: "var(--mly-teal-050)", fg: "var(--mly-teal-700)" },
  amber: { bg: "var(--cortex-amber-50)", fg: "var(--cortex-amber-600)" },
  real: { bg: "var(--cortex-amber-500)", fg: "var(--mly-ink-900)" },
  success: { bg: "#E0F2F1", fg: "var(--mly-success)" },
  danger: { bg: "#FFEBEE", fg: "var(--mly-danger)" },
  onDark: { bg: "rgba(255,255,255,0.12)", fg: "rgba(255,255,255,0.92)" },
};

export function Badge({
  children,
  color = "ink",
  style,
}: {
  children: ReactNode;
  color?: BadgeColor;
  style?: CSSProperties;
}) {
  const p = BADGE_PALETTE[color];
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        background: p.bg,
        color: p.fg,
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: "0.06em",
        textTransform: "uppercase",
        padding: "3px 8px",
        borderRadius: 3,
        ...style,
      }}
    >
      {children}
    </span>
  );
}

export function IntentPill({ intent }: { intent: keyof typeof INTENT_COLOR }) {
  const c = INTENT_COLOR[intent];
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        background: c.bg,
        color: c.fg,
        fontSize: 11,
        fontWeight: 600,
        padding: "2px 9px",
        borderRadius: 999,
      }}
    >
      <span style={{ width: 5, height: 5, borderRadius: "50%", background: c.fg }} />
      {intent}
    </span>
  );
}

export function CountUp({
  to,
  suffix = "",
  decimals = 0,
  duration = 600,
}: {
  to: number;
  suffix?: string;
  decimals?: number;
  duration?: number;
}) {
  const [v, setV] = useState(0);
  useEffect(() => {
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setV(to * eased);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [to, duration]);
  const formatted = v.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
  return (
    <span>
      {formatted}
      {suffix}
    </span>
  );
}

export function Toggle({
  on,
  onChange,
  size = "md",
}: {
  on: boolean;
  onChange: () => void;
  size?: "md" | "sm";
}) {
  const w = size === "sm" ? 38 : 46;
  const h = size === "sm" ? 22 : 26;
  const dot = h - 4;
  return (
    <button
      type="button"
      onClick={onChange}
      aria-pressed={on}
      style={{
        width: w,
        height: h,
        borderRadius: 999,
        border: "none",
        cursor: "pointer",
        background: on ? "var(--mly-teal-600)" : "var(--mly-ink-200)",
        position: "relative",
        transition: "all 200ms",
        boxShadow: on ? "inset 0 0 0 1px var(--mly-teal-700)" : "inset 0 0 0 1px var(--mly-ink-300)",
        flexShrink: 0,
      }}
    >
      <span
        style={{
          position: "absolute",
          top: 2,
          left: on ? w - dot - 2 : 2,
          width: dot,
          height: dot,
          borderRadius: "50%",
          background: "#fff",
          transition: "all 200ms",
          boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
          display: "grid",
          placeItems: "center",
          color: on ? "var(--mly-teal-700)" : "var(--mly-ink-500)",
        }}
      >
        <Icon name={on ? "check" : "remove"} size={11} />
      </span>
    </button>
  );
}

export function StepRail({
  step,
  steps,
}: {
  step: RailIndex;
  steps: readonly string[];
}) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      {steps.map((s, i) => {
        const done = i < step;
        const active = i === step;
        // Light Edition (handoff §3.3): completed = gold + white check,
        // active = solid brand-teal disc + white number, future = outlined
        // paper-border with paper-ink-3 number. Connector = paper-border.
        const discBg = done
          ? "var(--gold)"
          : active
            ? "var(--brand-teal)"
            : "transparent";
        const discBorder = done
          ? "var(--gold)"
          : active
            ? "var(--brand-teal)"
            : "var(--paper-border)";
        const discFg = done || active ? "#fff" : "var(--paper-ink-3)";
        const labelColor = active ? "var(--paper-ink)" : "var(--paper-ink-3)";
        return (
          <span key={s} style={{ display: "inline-flex", alignItems: "center", gap: 10 }}>
            <span
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <span
                style={{
                  width: 24,
                  height: 24,
                  borderRadius: "50%",
                  background: discBg,
                  border: `1.5px solid ${discBorder}`,
                  color: discFg,
                  display: "grid",
                  placeItems: "center",
                  fontSize: 11,
                  fontWeight: 700,
                  fontFamily: "var(--font-numeric)",
                }}
              >
                {done ? <Icon name="check" size={14} /> : i + 1}
              </span>
              <span
                style={{
                  fontSize: 12,
                  fontWeight: active ? 700 : 500,
                  color: labelColor,
                  letterSpacing: "0.01em",
                }}
              >
                {s}
              </span>
            </span>
            {i < steps.length - 1 ? (
              <span style={{ width: 22, height: 1, background: "var(--paper-border)" }} />
            ) : null}
          </span>
        );
      })}
    </div>
  );
}

function LangSwitch({
  current,
  targetHref,
}: {
  current: "en" | "zh";
  // Caller supplies a fully-typed Route so Next's typedRoutes can validate
  // the href at build time. Do not re-internalise the paths here — a ternary
  // on string literals inside this component collapses to `string` and fails
  // the Link prop check.
  targetHref: Route;
}) {
  const isEn = current === "en";
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        fontSize: 11,
        fontFamily: "var(--font-mono)",
        color: "var(--paper-ink-3)",
        padding: "5px 10px",
        border: "1px solid var(--paper-border)",
        borderRadius: 999,
        background: "#fff",
      }}
    >
      <span style={{ color: "var(--paper-ink)", fontWeight: 700 }}>{isEn ? "EN" : "繁中"}</span>
      <span aria-hidden style={{ color: "var(--paper-border)" }}>|</span>
      <Link
        href={targetHref}
        style={{
          color: "var(--paper-ink-3)",
          textDecoration: "none",
          fontWeight: 500,
        }}
      >
        {isEn ? "繁中" : "EN"}
      </Link>
    </span>
  );
}

export function TopBar({
  railStep,
  steps,
  onSkip,
  onExit,
  lang = "en",
  showDemoBadge = false,
  langSwitchHref = "/onboarding/v2/zh-TW" as Route,
}: {
  railStep: RailIndex;
  steps: readonly string[];
  onSkip: () => void;
  onExit: () => void;
  lang?: "en" | "zh";
  showDemoBadge?: boolean;
  langSwitchHref?: Route;
}) {
  return (
    <div
      style={{
        // Light Edition (handoff §3.3): white surface + paper-border seam.
        // The deep-teal gradient was replaced with a paper-ink-on-white
        // contract so the rail reads as a documentary header, not a banner.
        background: "#fff",
        color: "var(--paper-ink)",
        padding: "14px 0",
        borderBottom: "1px solid var(--paper-border)",
        position: "sticky",
        top: 0,
        zIndex: 50,
        boxShadow: "0 1px 0 rgba(var(--paper-ink-rgb), 0.02)",
      }}
    >
      <div
        className="onb-rail"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 28,
        }}
      >
        <button
          type="button"
          onClick={onExit}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            background: "transparent",
            border: "none",
            color: "var(--paper-ink)",
            cursor: "pointer",
            padding: 0,
            fontFamily: "inherit",
          }}
        >
          {/* mlytics wordmark — real brand PNG shipped from design handoff
              (web/public/brand/mlytics-logo.png, 500×90, ≈5.56:1 aspect).
              The PNG already contains the logo mark + "mlytics" text, so the
              previous inline-SVG "M" lockup and the "mlytics · cortex"
              wordmark span are gone. The `data-mly-mark="lockup"` hook is
              preserved on the <Image> for primitives test stability. */}
          <Image
            src="/brand/mlytics-logo.png"
            alt="mlytics"
            width={140}
            height={25}
            priority
            data-mly-mark="lockup"
            style={{ flexShrink: 0, height: "auto" }}
          />
          <span style={{ textAlign: "left" }}>
            <span
              style={{
                fontSize: 11,
                color: "var(--paper-ink-3)",
                display: "block",
              }}
            >
              Brand setup · First-time
            </span>
          </span>
          {showDemoBadge ? <Badge color="ink" style={{ marginLeft: 10 }}>Demo</Badge> : null}
        </button>
        <StepRail step={railStep} steps={steps} />
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span
            style={{
              fontSize: 11,
              color: "var(--paper-ink-3)",
              fontFamily: "var(--font-mono)",
            }}
          >
            ~5 minutes
          </span>
          <LangSwitch current={lang} targetHref={langSwitchHref} />
          <button
            type="button"
            onClick={onSkip}
            style={{
              // soft variant — white surface + paper-border + paper-ink-2.
              background: "#fff",
              color: "var(--paper-ink-2)",
              border: "1px solid var(--paper-border)",
              padding: "7px 14px",
              borderRadius: 6,
              cursor: "pointer",
              fontSize: 12,
              fontWeight: 600,
              fontFamily: "inherit",
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            Set up later
          </button>
        </div>
      </div>
    </div>
  );
}

export function StepHead({
  eyebrow,
  title,
  subtitle,
  accent,
}: {
  eyebrow: string;
  title: ReactNode;
  subtitle?: ReactNode;
  accent?: string;
}) {
  return (
    <div style={{ marginBottom: 24 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
        <Badge color="amber">{eyebrow}</Badge>
        {accent ? (
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mly-ink-500)" }}>
            {accent}
          </span>
        ) : null}
      </div>
      <h2
        style={{
          fontSize: 28,
          fontWeight: 700,
          color: "var(--mly-ink-900)",
          letterSpacing: "-0.015em",
          lineHeight: 1.2,
          marginBottom: 8,
          margin: 0,
        }}
      >
        {title}
      </h2>
      {subtitle ? (
        <p
          style={{
            color: "var(--mly-ink-600)",
            fontSize: 15,
            maxWidth: 760,
            margin: "8px 0 0",
            lineHeight: 1.55,
          }}
        >
          {subtitle}
        </p>
      ) : null}
    </div>
  );
}
