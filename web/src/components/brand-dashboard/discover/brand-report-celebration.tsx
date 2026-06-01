"use client";

/**
 * BrandReportCelebration — full-screen one-time celebration modal overlay.
 *
 * Shown only when ui-state `celebratePending` is true (first Discover entry
 * after onboarding). Accessible: Esc dismisses; focus is trapped inside the
 * dialog; role="dialog" + aria-modal + aria-labelledby.
 *
 * No shadcn Dialog primitive — we build a minimal accessible overlay
 * as instructed: Escape key + focus management.
 *
 * Dismiss triggers: Esc, close ×, "先看 Dashboard" button, download link.
 * Any dismiss → calls onClose (→ celebrate-consume server action).
 */

import { useEffect, useRef, type ReactElement } from "react";
import Link from "next/link";
import type { ReportEnvelope } from "@/app/brand/dashboard/report-types";
import { BrandConstellation } from "./brand-constellation";

// ── Confetti ───────────────────────────────────────────────────────────────

const CONFETTI_PALETTE = [
  "var(--gold)",
  "var(--brand-teal)",
  "var(--lime-deep)",
  "var(--paper-border)",
];

// Pre-generated at module load — stable across re-renders (no Math.random in render).
const CONFETTI_ITEMS = Array.from({ length: 50 }, (_, i) => ({
  left: (i * 2.1 + 3) % 100,
  top: (i * 3.7 + 7) % 100,
  rot: (i * 41) % 360,
  color: CONFETTI_PALETTE[i % CONFETTI_PALETTE.length],
  size: 4 + (i % 5) * 1.6,
  delay: (i % 10) * 0.2,
  dur: 3 + (i % 7) * 0.43,
}));

function BRConfetti(): ReactElement {
  const items = CONFETTI_ITEMS;
  return (
    <div
      aria-hidden
      style={{
        position: "absolute",
        inset: 0,
        overflow: "hidden",
        pointerEvents: "none",
      }}
    >
      {items.map((p, i) => (
        <span
          key={i}
          style={{
            position: "absolute",
            left: `${p.left}%`,
            top: `${p.top}%`,
            width: p.size,
            height: p.size * 0.4,
            background: p.color,
            transform: `rotate(${p.rot}deg)`,
            borderRadius: 1,
            animation: `br-confetti ${p.dur}s ease-in-out ${p.delay}s infinite`,
            opacity: 0.85,
          }}
        />
      ))}
    </div>
  );
}

// ── Public component ───────────────────────────────────────────────────────

export interface BrandReportCelebrationProps {
  report: ReportEnvelope;
  onClose: () => void;
}

const TITLE_ID = "br-celebration-title";

/**
 * BrandReportCelebration — one-time post-onboarding celebration modal.
 *
 * Viewport: designed for ≥1320px (matches the .geo-app desktop floor). Below
 * that, the modal becomes scrollable (overflow: auto on the outer dialog) so
 * content remains reachable, but optimal layout is desktop-first by design.
 *
 * Accessibility: role="dialog" + aria-modal + focus trap + Esc to dismiss.
 */
export function BrandReportCelebration({
  report,
  onClose,
}: BrandReportCelebrationProps): ReactElement {
  const overlayRef = useRef<HTMLDivElement>(null);
  const closeBtnRef = useRef<HTMLButtonElement>(null);

  const meta = report.report?.meta;
  const subject = meta?.subject ?? "你的品牌";
  const mono = meta?.monogram ?? subject.charAt(0).toUpperCase();
  const pageCount = meta?.pageCount ?? 0;
  const reportId = report.reportId;

  // Focus management — move focus to the close button on mount.
  useEffect(() => {
    closeBtnRef.current?.focus();
  }, []);

  // Esc dismisses; Tab / Shift-Tab are trapped within the dialog.
  //
  // This IS a real modal (aria-modal), so a proper focus trap is required:
  // without it, Tab walks into the page elements rendered behind the overlay
  // even though they're visually obscured — a screen-reader / keyboard a11y
  // failure. We query the dialog's focusable elements on each Tab and wrap
  // focus at the boundaries (last → first on Tab, first → last on Shift-Tab).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key !== "Tab") return;

      const root = overlayRef.current;
      if (!root) return;
      const focusable = root.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])',
      );
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement;

      if (e.shiftKey) {
        // Shift-Tab from the first element wraps to the last.
        if (active === first || !root.contains(active)) {
          e.preventDefault();
          last.focus();
        }
      } else {
        // Tab from the last element wraps to the first.
        if (active === last || !root.contains(active)) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  // Stat counts. Empty envelope sections fall back to 0 so the grid cell
  // always renders (per spec acceptance criterion).
  const reportInner = report.report ?? null;
  const counts = {
    productLines: reportInner?.productLines?.length ?? 0,
    mediaNetwork: reportInner?.mediaNetwork?.length ?? 0,
    competitors:  reportInner?.competitors?.length  ?? 0,
    risks:        reportInner?.risks?.length        ?? 0,
  };

  return (
    <div
      ref={overlayRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby={TITLE_ID}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1000,
        background:
          "radial-gradient(circle at 50% 35%, #FBF6E8 0%, var(--paper) 55%, var(--paper-warm) 100%)",
        color: "var(--paper-ink)",
        overflowY: "auto",
        animation: "br-fade-in 320ms ease-out",
      }}
    >
      {/* Warm faint grid (decoration only) */}
      <div
        aria-hidden
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(110,96,69,0.06) 1px, transparent 1px)," +
            "linear-gradient(90deg, rgba(110,96,69,0.06) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
          maskImage: "radial-gradient(ellipse at center, #000 30%, transparent 75%)",
          WebkitMaskImage: "radial-gradient(ellipse at center, #000 30%, transparent 75%)",
        }}
      />

      <BRConfetti />

      {/* Top bar */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          padding: "16px 28px",
          display: "flex",
          alignItems: "center",
          gap: 12,
          zIndex: 5,
        }}
      >
        <div
          style={{
            width: 26,
            height: 26,
            borderRadius: 5,
            background: "var(--brand-teal)",
            color: "#fff",
            display: "grid",
            placeItems: "center",
            fontWeight: 800,
            fontSize: 13,
          }}
        >
          {mono}
        </div>
        <div
          style={{
            fontSize: 12,
            color: "var(--paper-ink-3)",
            fontFamily: "var(--font-mono)",
            letterSpacing: "0.14em",
            textTransform: "uppercase",
          }}
        >
          Cortex · Brand Agent · Live
        </div>
        <button
          ref={closeBtnRef}
          aria-label="關閉"
          onClick={onClose}
          style={{
            background: "transparent",
            border: "none",
            color: "var(--paper-ink-3)",
            cursor: "pointer",
            marginLeft: "auto",
            padding: 4,
          }}
        >
          <span className="material-icons-outlined" style={{ fontSize: 20, color: "var(--paper-ink-3)" }}>
            close
          </span>
        </button>
      </div>

      {/* Main two-column body */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "grid",
          gridTemplateColumns: "1.05fr 0.95fr",
          alignItems: "center",
          padding: "0 80px",
        }}
      >
        {/* LEFT — constellation + radar rings + gold orbit ray */}
        <div style={{ position: "relative", display: "grid", placeItems: "center" }}>
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              aria-hidden
              style={{
                position: "absolute",
                width: 560,
                height: 560,
                borderRadius: "50%",
                border: "1px solid rgba(185,136,33,0.20)",
                opacity: 0.8 - i * 0.2,
                animation: `mly-pulse ${2.2 + i * 0.4}s ease-in-out infinite`,
              }}
            />
          ))}
          <div
            style={{
              position: "relative",
              animation: "mly-pop-in 800ms cubic-bezier(0.2,0.9,0.3,1.2) backwards",
            }}
          >
            <BrandConstellation size={520} mono={mono} accent="var(--brand-teal)" showConnectorLines />
            <div
              aria-hidden
              style={{
                position: "absolute",
                inset: 0,
                borderRadius: "50%",
                background:
                  "conic-gradient(from 0deg, rgba(185,136,33,0.20), transparent 30%)",
                animation: "br-orbit 5s linear infinite",
                pointerEvents: "none",
              }}
            />
          </div>
        </div>

        {/* RIGHT — copy + stats + CTAs */}
        <div style={{ paddingLeft: 28 }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              padding: "6px 12px",
              background: "var(--gold-soft)",
              border: "1px solid var(--gold-border)",
              borderRadius: 999,
              color: "var(--gold-deep)",
              fontSize: 11,
              fontFamily: "var(--font-mono)",
              letterSpacing: "0.16em",
              textTransform: "uppercase",
              marginBottom: 18,
              fontWeight: 700,
            }}
          >
            <span className="material-icons-outlined" style={{ fontSize: 13, color: "var(--gold-deep)" }}>
              auto_awesome
            </span>
            成就解鎖 · Brand IQ 報告
          </div>

          <div
            style={{
              fontSize: 14,
              color: "var(--paper-ink-3)",
              fontFamily: "var(--font-mono)",
              marginBottom: 6,
              letterSpacing: "0.06em",
            }}
          >
            這是你的品牌的形狀——
          </div>
          <h1
            id={TITLE_ID}
            style={{
              fontFamily: "var(--font-serif-tc)",
              fontSize: 52,
              fontWeight: 700,
              letterSpacing: "-0.02em",
              lineHeight: 1.05,
              marginBottom: 14,
              color: "var(--paper-ink)",
            }}
          >
            {subject}
            <br />
            <span
              style={{
                fontFamily: "var(--font-serif)",
                fontWeight: 500,
                fontStyle: "italic",
                color: "var(--gold)",
              }}
            >
              Brand Constellation
            </span>
          </h1>
          <p
            style={{
              fontSize: 14,
              color: "var(--paper-ink-2)",
              lineHeight: 1.7,
              marginBottom: 24,
              maxWidth: 440,
            }}
          >
            Onboarding 階段我們找到了 {subject} 的核心、{counts.productLines} 條產品線、
            {counts.competitors} 家直接競品，以及 {counts.mediaNetwork} 家可分發的媒體節點。
            它們在這份 {pageCount} 頁的 Brand IQ 報告裡，被整理成一個你可以隨時拿給高層、夥伴看的故事。
          </p>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, 1fr)",
              gap: 14,
              marginBottom: 26,
              maxWidth: 480,
            }}
          >
            {[
              { label: "產品線", value: counts.productLines },
              { label: "媒體節點", value: counts.mediaNetwork },
              { label: "競品", value: counts.competitors },
              { label: "風險訊號", value: counts.risks },
            ].map((s) => (
              <div key={s.label}>
                <div
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 9,
                    letterSpacing: "0.14em",
                    textTransform: "uppercase",
                    color: "var(--paper-ink-3)",
                  }}
                >
                  {s.label}
                </div>
                <div
                  style={{
                    fontFamily: "var(--font-numeric)",
                    fontSize: 30,
                    fontWeight: 700,
                    color: "var(--paper-ink)",
                    lineHeight: 1,
                    marginTop: 4,
                  }}
                >
                  {s.value}
                </div>
              </div>
            ))}
          </div>

          <div style={{ display: "flex", gap: 10 }}>
            <Link
              href={`/brand/reports/${reportId}`}
              onClick={onClose}
              style={{
                background: "var(--gold)",
                color: "#fff",
                border: "none",
                padding: "14px 22px",
                borderRadius: 8,
                fontSize: 14,
                fontWeight: 800,
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                boxShadow: "0 8px 18px -4px rgba(185,136,33,0.45)",
                animation: "br-glow 2.6s ease-in-out infinite",
                textDecoration: "none",
              }}
            >
              <span className="material-icons-outlined" style={{ fontSize: 16, color: "#fff" }}>
                arrow_forward
              </span>
              查看 Brand IQ 報告
            </Link>
          </div>
          <div
            style={{
              marginTop: 14,
              fontSize: 11,
              color: "var(--paper-ink-3)",
              fontFamily: "var(--font-mono)",
              letterSpacing: "0.06em",
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <span className="material-icons-outlined" style={{ fontSize: 11, color: "var(--paper-ink-3)" }}>
              bookmark
            </span>
            已自動存到 Knowledge Base · 隨時可重新下載
          </div>
        </div>
      </div>

    </div>
  );
}
