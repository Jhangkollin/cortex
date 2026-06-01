"use client";

import type { ReportVersionItem } from "@/lib/cortex-api";
import { Icon } from "@/components/report-viewer/shared/icon";
import { isCurrent } from "./is-current";

interface FeaturedReportCardProps {
  version: ReportVersionItem;
}

/**
 * Featured card for the current Brand IQ report.
 * Shows a mini cover thumbnail, title, badges, and action buttons.
 */
export function FeaturedReportCard({ version }: FeaturedReportCardProps) {
  const previewHref = `/brand/reports/${version.reportId}`;
  const downloadHref = `/brand/reports/${version.reportId}/pdf`;

  // Format the date in a readable way (YYYY-MM-DD → YYYY-MM-DD, already fine)
  const formattedDate = version.createdAt
    ? new Date(version.createdAt).toLocaleDateString("zh-TW", {
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : "—";

  return (
    <div
      data-testid="featured-report-card"
      style={{
        padding: 20,
        borderRadius: 12,
        marginBottom: 16,
        background: "linear-gradient(135deg, var(--mly-teal-050) 0%, #fff 100%)",
        border: "1px solid var(--mly-teal-100)",
        display: "grid",
        gridTemplateColumns: "auto 1fr auto",
        gap: 18,
        alignItems: "center",
      }}
    >
      {/* Mini cover thumbnail */}
      <div
        aria-hidden="true"
        style={{
          width: 88,
          height: 116,
          borderRadius: 4,
          position: "relative",
          background: "linear-gradient(135deg, #06181A 0%, #0E2D2C 80%, #144948 100%)",
          color: "#fff",
          padding: "8px 6px",
          overflow: "hidden",
          boxShadow: "0 10px 18px -4px rgba(14,45,44,0.4)",
          fontFamily: "var(--font-serif-tc, serif)",
          flexShrink: 0,
        }}
      >
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 6,
            letterSpacing: "0.14em",
            color: "var(--mly-lime-200)",
            marginBottom: 4,
            fontWeight: 700,
          }}
        >
          BRAND IQ · {version.version}
        </div>
        <div style={{ fontSize: 11, fontWeight: 800, lineHeight: 1.2, color: "#fff" }}>
          Brand IQ
        </div>
        <div style={{ fontSize: 7, color: "rgba(255,255,255,0.7)", marginTop: 3 }}>
          The shape of a brand.
        </div>
        {/* Monogram circle */}
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: 60,
            transform: "translateX(-50%)",
            width: 48,
            height: 48,
            borderRadius: "50%",
            border: "1px solid rgba(124,179,66,0.4)",
            display: "grid",
            placeItems: "center",
          }}
        >
          <div
            style={{
              width: 18,
              height: 18,
              borderRadius: "50%",
              background: "#fff",
              display: "grid",
              placeItems: "center",
              fontWeight: 700,
              color: "#0E2D2C",
              fontFamily: "var(--font-serif, serif)",
              fontSize: 10,
            }}
          >
            B
          </div>
        </div>
      </div>

      {/* Info */}
      <div>
        <div
          style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6, flexWrap: "wrap" }}
        >
          {isCurrent(version) && (
            <span
              style={{
                padding: "2px 8px",
                borderRadius: 999,
                background: "var(--cortex-amber-50)",
                color: "var(--cortex-amber-600)",
                fontSize: 11,
                fontWeight: 700,
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
              }}
            >
              <Icon name="new_releases" size={11} color="var(--cortex-amber-600)" />
              最新
            </span>
          )}
          <span
            style={{
              padding: "2px 8px",
              borderRadius: 999,
              background: "var(--mly-ink-050)",
              color: "var(--mly-ink-700)",
              fontSize: 11,
              fontFamily: "var(--font-mono)",
              fontWeight: 600,
            }}
          >
            {version.version}
          </span>
          <span
            style={{
              padding: "2px 8px",
              borderRadius: 999,
              background: "var(--mly-ink-050)",
              color: "var(--mly-ink-700)",
              fontSize: 11,
              fontFamily: "var(--font-mono)",
              fontWeight: 600,
            }}
          >
            PDF
          </span>
        </div>

        <div
          style={{ fontSize: 17, fontWeight: 700, color: "var(--mly-ink-900)" }}
        >
          Brand IQ 報告 · {version.version}
        </div>

        <div
          style={{ fontSize: 12, color: "var(--mly-ink-500)", marginTop: 4 }}
        >
          產生於 {formattedDate} · 由 Cortex · Brand Agent 整理
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
        <a
          href={previewHref}
          data-testid="preview-link"
          style={{
            background: "transparent",
            color: "var(--mly-ink-700)",
            border: "1px solid var(--mly-ink-200)",
            padding: "10px 14px",
            borderRadius: 7,
            fontSize: 13,
            fontWeight: 600,
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            textDecoration: "none",
          }}
        >
          <Icon name="visibility" size={14} color="var(--mly-ink-700)" />
          預覽
        </a>
        <a
          href={downloadHref}
          data-testid="download-link"
          style={{
            background: "var(--mly-teal-700)",
            color: "#fff",
            border: "none",
            padding: "11px 16px",
            borderRadius: 7,
            fontSize: 13,
            fontWeight: 700,
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            textDecoration: "none",
          }}
        >
          <Icon name="download" size={14} color="#fff" />
          下載 PDF
        </a>
      </div>
    </div>
  );
}
