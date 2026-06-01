"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import type { BrandIqReport } from "@/lib/cortex-api";
import { Icon } from "./shared/icon";
import { SECTIONS } from "./sections";
import { Page1 } from "./pages/page-1";
import { Page2 } from "./pages/page-2";
import { Page3 } from "./pages/page-3";
import { Page4 } from "./pages/page-4";
import { Page5 } from "./pages/page-5";
import { Page6 } from "./pages/page-6";
import { Page7 } from "./pages/page-7";
import { Page8 } from "./pages/page-8";

interface ReportViewerProps {
  report: BrandIqReport;
  reportId: string;
}

/**
 * Client-only report viewer shell — Light Edition.
 *
 * Chrome: white toolbar with paper-border, cream TOC sidebar with gold-soft
 * active highlight, paper-warm scroll stage. The "Download PDF" button keeps
 * the ceremony role (solid gold + white text + gold drop-shadow); Print /
 * Share / Back affordances are soft (white + paper-border).
 *
 * Toolbar + left TOC (IntersectionObserver scroll-highlight) + centre page
 * stack. Zoom: 55–150% in 5% steps. Fit-to-width on resize (55–100% cap).
 */
export function ReportViewer({ report, reportId }: ReportViewerProps) {
  const router = useRouter();
  const b = report.meta;

  const [activePage, setActivePage] = useState(1);
  const [scale, setScale] = useState(0.85);
  const scrollRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<Record<number, HTMLDivElement | null>>({});

  /** Smooth-scroll to a page */
  const goTo = useCallback((n: number) => {
    const el = pageRefs.current[n];
    if (!el || !scrollRef.current) return;
    const top = el.offsetTop - 20;
    scrollRef.current.scrollTo({ top, behavior: "smooth" });
  }, []);

  /** IntersectionObserver — highlight TOC item matching most-visible page */
  useEffect(() => {
    const root = scrollRef.current;
    if (!root) return;
    const io = new IntersectionObserver(
      (entries) => {
        let bestN = activePage;
        let bestRatio = 0;
        entries.forEach((e) => {
          if (e.intersectionRatio > bestRatio) {
            bestRatio = e.intersectionRatio;
            bestN = parseInt((e.target as HTMLElement).dataset.page ?? "1", 10);
          }
        });
        if (bestN && bestRatio > 0.3) setActivePage(bestN);
      },
      { root, threshold: [0.3, 0.5, 0.7] },
    );
    Object.values(pageRefs.current).forEach((el) => el && io.observe(el));
    return () => io.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /** Fit-to-width on resize */
  useEffect(() => {
    const onResize = () => {
      const viewerW = window.innerWidth - 240 - 32;
      const fit = Math.min(1.0, Math.max(0.55, (viewerW - 24) / 794));
      setScale(fit);
    };
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  /** Escape returns to the dashboard so keyboard users can exit. */
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") router.back();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [router]);

  // Point at the Next route handler (NOT cortex-api directly) — it injects the
  // signed Bearer token server-side and streams the binary back.
  const pdfUrl = `/brand/reports/${reportId}/pdf`;

  // Soft (white + paper-border) toolbar button — reused by Back, Print, Share.
  const softBtnStyle = {
    display: "inline-flex" as const,
    alignItems: "center" as const,
    gap: 6,
    background: "#fff",
    border: "1px solid #d5dee0",
    color: "var(--mly-ink-800)",
    padding: "7px 12px",
    borderRadius: 6,
    fontSize: 12,
    fontWeight: 600,
    cursor: "pointer" as const,
  };

  return (
    // Full-page route overlay — a labelled region, NOT a modal (we don't trap
    // focus or implement modal semantics). Escape navigates back (see effect).
    <section
      aria-label={`${b.subject} · Brand IQ 報告`}
      style={{
        position: "fixed",
        inset: 0,
        background: "#f8f8f6",
        color: "var(--mly-ink-800)",
        display: "flex",
        flexDirection: "column",
        // Above the shell chrome: drawer trigger=100, modal=90, drawer=80.
        zIndex: 110,
      }}
    >
      {/* ── Toolbar ── */}
      <div
        className="report-toolbar"
        style={{
          height: 60,
          padding: "0 18px",
          display: "flex",
          alignItems: "center",
          gap: 14,
          background: "#fff",
          borderBottom: "1px solid #d5dee0",
          flexShrink: 0,
        }}
      >
        {/* back */}
        <button
          onClick={() => router.back()}
          style={{
            ...softBtnStyle,
            background: "transparent",
          }}
        >
          <Icon name="arrow_back" size={14} color="var(--mly-ink-800)" /> 返回 Dashboard
        </button>

        <div style={{ width: 1, height: 22, background: "#d5dee0" }} />

        {/* brand monogram + title */}
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div
            style={{
              width: 30,
              height: 30,
              borderRadius: 6,
              background: "var(--mly-teal-700)",
              color: "#fff",
              display: "grid",
              placeItems: "center",
              fontWeight: 800,
              fontSize: 14,
              flexShrink: 0,
            }}
          >
            {b.monogram}
          </div>
          <div style={{ lineHeight: 1.2 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--mly-ink-800)" }}>
              {b.subject} · Brand IQ 報告
            </div>
            <div
              style={{
                fontSize: 10,
                fontFamily: "var(--font-mono)",
                color: "var(--mly-ink-400)",
                letterSpacing: "0.1em",
              }}
            >
              {b.reportId} · {b.reportDate} · {b.preparedBy}
            </div>
          </div>
        </div>

        {/* page counter + zoom */}
        <div
          style={{
            marginLeft: "auto",
            display: "flex",
            alignItems: "center",
            gap: 14,
            fontFamily: "var(--font-mono)",
            fontSize: 11,
            color: "var(--mly-ink-400)",
          }}
        >
          <span>
            第 {activePage} / {SECTIONS.length} 頁
          </span>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <button
              aria-label="縮小"
              onClick={() => setScale((s) => Math.max(0.55, parseFloat((s - 0.05).toFixed(2))))}
              style={{
                background: "#fff",
                border: "1px solid #d5dee0",
                color: "var(--mly-ink-800)",
                width: 24,
                height: 24,
                borderRadius: 4,
                cursor: "pointer",
                display: "grid",
                placeItems: "center",
              }}
            >
              <Icon name="remove" size={12} color="var(--mly-ink-800)" />
            </button>
            <span style={{ minWidth: 36, textAlign: "center" }}>
              {Math.round(scale * 100)}%
            </span>
            <button
              aria-label="放大"
              onClick={() => setScale((s) => Math.min(1.5, parseFloat((s + 0.05).toFixed(2))))}
              style={{
                background: "#fff",
                border: "1px solid #d5dee0",
                color: "var(--mly-ink-800)",
                width: 24,
                height: 24,
                borderRadius: 4,
                cursor: "pointer",
                display: "grid",
                placeItems: "center",
              }}
            >
              <Icon name="add" size={12} color="var(--mly-ink-800)" />
            </button>
          </div>
        </div>

        <div style={{ width: 1, height: 22, background: "#d5dee0" }} />

        {/* print */}
        <button onClick={() => window.print()} style={softBtnStyle}>
          <Icon name="print" size={14} color="var(--mly-ink-800)" /> 列印
        </button>

        {/* download PDF — ceremony CTA: solid gold + white text + gold drop-shadow.
            Surface uses --gold-deep (not --gold) so #fff text hits ~7:1 contrast
            (AAA). Handoff §5 says "主 CTA → --gold 實心 + 白字"; we diverge on the
            shade because plain --gold on #fff only reaches ~4.1:1 and fails WCAG
            AA. Visual semantics (ceremony gold solid) are unchanged. */}
        <a
          href={pdfUrl}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            background: "var(--mly-teal-700)",
            color: "#fff",
            border: "none",
            padding: "8px 16px",
            borderRadius: 6,
            fontSize: 13,
            fontWeight: 800,
            cursor: "pointer",
            textDecoration: "none",
            boxShadow: "0 6px 16px -4px rgba(28, 114, 107, 0.30)",
          }}
        >
          <Icon name="download" size={15} color="#fff" /> 下載 PDF · 8 頁
        </a>
      </div>

      {/* ── Body: TOC + pages ── */}
      <div
        style={{ flex: 1, display: "grid", gridTemplateColumns: "240px 1fr", minHeight: 0 }}
      >
        {/* ── Left TOC ── */}
        <aside
          className="report-toc"
          style={{
            background: "#f5f9f8",
            borderRight: "1px solid #d5dee0",
            overflowY: "auto",
            padding: "20px 16px",
          }}
        >
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 10,
              letterSpacing: "0.2em",
              textTransform: "uppercase",
              color: "var(--mly-ink-400)",
              marginBottom: 10,
              fontWeight: 700,
            }}
          >
            Table of Contents
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            {SECTIONS.map((p) => {
              const on = p.n === activePage;
              return (
                <button
                  key={p.n}
                  onClick={() => goTo(p.n)}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "26px 1fr auto",
                    gap: 8,
                    alignItems: "center",
                    padding: "9px 10px",
                    borderRadius: 6,
                    cursor: "pointer",
                    textAlign: "left",
                    background: on ? "rgb(244, 249, 250)" : "transparent",
                    border: `1px solid ${on ? "var(--mly-teal-200)" : "transparent"}`,
                    color: "var(--mly-ink-800)",
                    transition: "all 150ms",
                  }}
                >
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: 10,
                      color: on ? "var(--mly-teal-700)" : "var(--mly-ink-400)",
                      fontWeight: 700,
                    }}
                  >
                    {String(p.n).padStart(2, "0")}
                  </span>
                  <span>
                    <div
                      style={{
                        fontSize: 12.5,
                        fontWeight: on ? 700 : 500,
                        color: "var(--mly-ink-800)",
                      }}
                    >
                      {p.toc}
                    </div>
                    <div
                      style={{
                        fontSize: 10,
                        fontFamily: "var(--font-mono)",
                        color: "var(--mly-ink-400)",
                        marginTop: 1,
                        letterSpacing: "0.06em",
                      }}
                    >
                      {p.tocEn}
                    </div>
                  </span>
                  {on ? (
                    <span
                      style={{
                        width: 5,
                        height: 5,
                        borderRadius: "50%",
                        background: "var(--mly-teal-400)",
                        boxShadow: "0 0 8px var(--mly-teal-400)",
                      }}
                    />
                  ) : null}
                </button>
              );
            })}
          </div>

          {/* mini summary */}
          <div
            style={{
              marginTop: 18,
              paddingTop: 18,
              borderTop: "1px solid #d5dee0",
            }}
          >
            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 10,
                letterSpacing: "0.2em",
                textTransform: "uppercase",
                color: "var(--mly-ink-400)",
                marginBottom: 8,
                fontWeight: 700,
              }}
            >
              Report at a glance
            </div>
            {[
              ["產品線", String(report.productLines.length)],
              ["媒體節點", String(report.mediaNetwork.length)],
              ["競品", String(report.competitors.length)],
              ["風險訊號", String(report.risks.length)],
              ["資料品質", `${b.confidence ?? "—"}% 信心`],
            ].map(([l, v]) => (
              <div
                key={l}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: 11,
                  color: "var(--mly-ink-600)",
                  padding: "4px 0",
                }}
              >
                <span>{l}</span>
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    color: "var(--mly-ink-800)",
                    fontWeight: 700,
                  }}
                >
                  {v}
                </span>
              </div>
            ))}
          </div>

          <div
            style={{
              marginTop: 18,
              padding: "12px 12px",
              background: "rgb(244, 249, 250)",
              border: "1px dashed var(--mly-teal-200)",
              borderRadius: 6,
              fontSize: 11,
              color: "var(--mly-ink-600)",
              lineHeight: 1.55,
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <Icon name="bookmark" size={12} color="var(--mly-teal-700)" />
            已存到 Knowledge Base · 隨時可重新下載
          </div>
        </aside>

        {/* ── Center page stack ── */}
        <div
          ref={scrollRef}
          className="report-page-stack"
          style={{
            overflowY: "auto",
            padding: "24px 16px 80px",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          {SECTIONS.map((p) => {
            const PageComp = PAGE_COMPONENTS[p.n];
            if (!PageComp) return null;
            return (
              <div
                key={p.n}
                ref={(el) => {
                  pageRefs.current[p.n] = el;
                }}
                data-page={p.n}
                className="report-page-wrapper"
                style={{
                  width: 794 * scale,
                  height: 1123 * scale,
                  marginBottom: 28,
                  position: "relative",
                  flexShrink: 0,
                }}
              >
                <div
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    transform: `scale(${scale})`,
                    transformOrigin: "top left",
                  }}
                >
                  <div
                    style={{
                      position: "relative",
                      boxShadow:
                        "0 4px 24px rgba(80, 100, 110, 0.18), 0 0 0 1px rgba(100, 120, 130, 0.08)",
                    }}
                  >
                    <PageComp report={report} />
                  </div>
                </div>
                {/* page label above */}
                <div
                  style={{
                    position: "absolute",
                    top: -22,
                    left: 0,
                    right: 0,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    fontFamily: "var(--font-mono)",
                    fontSize: 10,
                    letterSpacing: "0.16em",
                    textTransform: "uppercase",
                    color: "var(--mly-ink-400)",
                  }}
                >
                  <span>
                    p.{String(p.n).padStart(2, "0")} · {p.tocEn}
                  </span>
                  <span>{p.toc}</span>
                </div>
              </div>
            );
          })}

          {/* end of document */}
          <div
            style={{
              width: 794 * scale,
              padding: "20px 16px",
              textAlign: "center",
              color: "var(--mly-ink-400)",
              fontFamily: "var(--font-mono)",
              fontSize: 11,
              borderTop: "1px dashed #d5dee0",
              letterSpacing: "0.14em",
            }}
          >
            — END OF REPORT · Cortex Brand Intelligence —
          </div>
        </div>
      </div>

      {/* ── Print styles ── */}
      <style>{`
        @media print {
          .report-toolbar,
          .report-toc { display: none !important; }
          .report-page-stack {
            display: block !important;
            overflow: visible !important;
            padding: 0 !important;
          }
          .report-page-wrapper {
            page-break-after: always;
            break-after: page;
            width: 794px !important;
            height: 1123px !important;
          }
          .report-page-wrapper > div {
            transform: none !important;
          }
        }
      `}</style>
    </section>
  );
}

/** Map page number to component — keeps the viewer shell lean. */
const PAGE_COMPONENTS: Record<number, React.ComponentType<{ report: BrandIqReport }>> = {
  1: Page1,
  2: Page2,
  3: Page3,
  4: Page4,
  5: Page5,
  6: Page6,
  7: Page7,
  8: Page8,
};
