"use client";

/**
 * BrandReportHero — dismissable hero card sitting at the top of DiscoverDashboard.
 *
 * States:
 *   generating → skeleton with "準備中…" copy
 *   failed     → error state with retry CTA (calls onRetry)
 *   ready      → full card with view + download CTAs
 *   hidden     → null (heroDismissed == true)
 *
 * All brand-specific copy comes from the real report envelope — no fixtures.
 * The × dismiss calls onDismiss (→ server action → api hero-dismiss endpoint).
 */

import type { ReactElement } from "react";
import Link from "next/link";
import type { ReportEnvelope } from "@/app/brand/dashboard/report-types";

// ── Skeleton state ─────────────────────────────────────────────────────────

function GeneratingSkeleton(): ReactElement {
  return (
    <div
      style={{
        position: "relative",
        borderRadius: 14,
        overflow: "hidden",
        background: "var(--paper)",
        color: "var(--paper-ink)",
        padding: 26,
        marginBottom: 24,
        minHeight: 188,
        border: "1px solid var(--paper-border)",
        boxShadow: "0 16px 32px -8px rgba(110,96,69,0.18)",
      }}
    >
      <div
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: 11,
          letterSpacing: "0.14em",
          textTransform: "uppercase",
          color: "var(--paper-ink-3)",
          marginBottom: 12,
        }}
      >
        準備中 · Brand IQ 報告
      </div>
      {[260, 360, 220].map((w, i) => (
        <div
          key={i}
          style={{
            height: 18,
            width: w,
            borderRadius: 6,
            marginBottom: 10,
            background:
              "linear-gradient(90deg, var(--paper-warm) 0%, var(--paper) 50%, var(--paper-warm) 100%)",
            backgroundSize: "480px 100%",
            animation: "br-shimmer 1.4s linear infinite",
          }}
        />
      ))}
    </div>
  );
}

// ── Failed state ───────────────────────────────────────────────────────────

interface FailedStateProps {
  report: ReportEnvelope;
  onRetry: () => void;
  onDismiss: () => void;
}

function FailedState({
  report,
  onRetry,
  onDismiss,
}: FailedStateProps): ReactElement {
  const errorMsg = report.error ?? "未知錯誤";
  return (
    <div
      style={{
        position: "relative",
        borderRadius: 14,
        overflow: "hidden",
        background: "var(--paper)",
        color: "var(--paper-ink)",
        padding: 26,
        marginBottom: 24,
        minHeight: 188,
        border: "1px solid var(--paper-border)",
        boxShadow: "0 16px 32px -8px rgba(110,96,69,0.18)",
      }}
    >
      <button
        type="button"
        aria-label="關閉"
        onClick={onDismiss}
        style={{
          position: "absolute",
          top: 14,
          right: 14,
          background: "transparent",
          border: "none",
          padding: 6,
          borderRadius: 6,
          cursor: "pointer",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          color: "var(--paper-ink-4)",
        }}
      >
        <span className="material-icons-outlined" style={{ fontSize: 18 }}>close</span>
      </button>
      <div
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: 11,
          letterSpacing: "0.14em",
          textTransform: "uppercase",
          color: "var(--paper-ink-3)",
          marginBottom: 8,
        }}
      >
        Brand IQ 報告 · 生成失敗
      </div>
      <div
        style={{
          fontSize: 13,
          color: "var(--paper-ink-2)",
          marginBottom: 16,
          maxWidth: 580,
        }}
      >
        {errorMsg}
      </div>
      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <button
          type="button"
          onClick={onRetry}
          aria-label="重試"
          style={{
            background: "var(--gold)",
            color: "#fff",
            border: "none",
            padding: "10px 16px",
            borderRadius: 8,
            fontSize: 13,
            fontWeight: 800,
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: 7,
          }}
        >
          <span className="material-icons-outlined" style={{ fontSize: 15, color: "#fff" }}>
            refresh
          </span>
          重試
        </button>
      </div>
    </div>
  );
}

// ── Ready state ────────────────────────────────────────────────────────────

interface ReadyHeroProps {
  report: ReportEnvelope;
  onDismiss: () => void;
}

function ReadyHero({ report, onDismiss }: ReadyHeroProps): ReactElement {
  const meta = report.report?.meta;
  const subject  = meta?.subject  ?? "你的品牌";
  const mono     = meta?.monogram ?? subject.charAt(0).toUpperCase();
  const pageCount = meta?.pageCount ?? 0;
  const reportDate = meta?.reportDate ?? "—";
  const preparedBy = meta?.preparedBy ?? "Cortex";
  const domain    = meta?.domain ?? null;
  const reportId   = report.reportId;

  return (
    <>
    <div
      style={{
        fontFamily: "var(--font-mono)",
        fontSize: 14,
        fontWeight: 700,
        letterSpacing: "0.12em",
        textTransform: "uppercase",
        color: "var(--mly-teal-700)",
        marginBottom: 40,
      }}
    >
      BRAND CORTEX{domain ? <span style={{ color: "var(--mly-ink-400)", fontWeight: 400, letterSpacing: 0, textTransform: "none" }}>: {domain}</span> : null}
    </div>
    <div
      style={{
        position: "relative",
        borderRadius: 14,
        overflow: "hidden",
        background: "#f7c465",
        color: "var(--paper-ink)",
        padding: 26,
        marginBottom: 64,
        minHeight: 188,
        border: "1px solid #f7c465",
        boxShadow: "0 12px 28px -6px rgba(180,140,50,0.22)",
      }}
    >
      <button
        type="button"
        aria-label="關閉"
        onClick={onDismiss}
        style={{
          position: "absolute",
          top: 14,
          right: 14,
          background: "transparent",
          border: "none",
          padding: 6,
          borderRadius: 6,
          cursor: "pointer",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          color: "rgba(0,0,0,0.45)",
        }}
      >
        <span className="material-icons-outlined" style={{ fontSize: 18 }}>close</span>
      </button>

      <div style={{ position: "relative", paddingRight: 40 }}>
        <h2
          style={{
            fontSize: 30,
            fontWeight: 800,
            letterSpacing: "-0.02em",
            lineHeight: 1.15,
            marginBottom: 8,
            color: "var(--paper-ink)",
          }}
        >
          {subject} 的品牌側寫已準備好，下載你的第一份報告
        </h2>
        <p
          style={{
            fontSize: 13,
            color: "var(--paper-ink-2)",
            lineHeight: 1.6,
            margin: 0,
          }}
        >
          從 onboarding 抓取的所有公開資料，已整理成 {pageCount} 頁的 PDF。
          適合給高層、外部夥伴、或保留作為 Brand Agent 啟動點的快照。
        </p>

        <div style={{ display: "flex", gap: 10, marginTop: 18, alignItems: "center" }}>
          <Link
            href={`/brand/reports/${reportId}`}
            style={{
              background: "#fff",
              color: "var(--mly-teal-800)",
              border: "none",
              padding: "11px 18px",
              borderRadius: 8,
              fontSize: 13,
              fontWeight: 700,
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: 7,
              textDecoration: "none",
              boxShadow: "0 6px 16px -3px rgba(20,73,72,0.20)",
            }}
          >
            <span className="material-icons-outlined" style={{ fontSize: 15, color: "var(--mly-teal-800)" }}>
              arrow_forward
            </span>
            查看 Brand IQ 報告
          </Link>
          <span
            style={{
              marginLeft: 12,
              fontSize: 11,
              color: "rgba(0,0,0,0.55)",
              fontFamily: "var(--font-mono)",
            }}
          >
            產生於 {reportDate} · {preparedBy}
          </span>
        </div>
      </div>
    </div>
    </>
  );
}

// ── Public component ───────────────────────────────────────────────────────

export interface BrandReportHeroProps {
  report: ReportEnvelope | null;
  heroDismissed: boolean;
  onDismiss: () => void;
  /** Re-trigger generation from the failed-state "重試" CTA. Required so the
   *  CTA always does something (no silent no-op). */
  onRetry: () => void;
}

export function BrandReportHero({
  report,
  heroDismissed,
  onDismiss,
  onRetry,
}: BrandReportHeroProps): ReactElement | null {
  if (heroDismissed) return null;
  if (report === null) return null; // No reports at all yet — silently hidden

  if (report.status === "pending" || report.status === "running") {
    return <GeneratingSkeleton />;
  }
  if (report.status === "failed") {
    return <FailedState report={report} onRetry={onRetry} onDismiss={onDismiss} />;
  }
  // ready
  return <ReadyHero report={report} onDismiss={onDismiss} />;
}
