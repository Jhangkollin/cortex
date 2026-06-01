"use client";

import type { CSSProperties } from "react";

import type { ReportVersionItem } from "@/lib/cortex-api";
import { Icon } from "@/components/report-viewer/shared/icon";
import { isCurrent } from "./is-current";

interface VersionHistoryTableProps {
  versions: ReportVersionItem[];
}

// Shared column template — header and every body row must stay aligned.
const GRID_COLUMNS = "100px 1fr 120px 100px";

// Single source of truth for the four header-cell styles (they only differ
// by their text content).
const headerCellStyle: CSSProperties = {
  fontSize: 11,
  fontWeight: 700,
  color: "var(--mly-ink-500)",
  fontFamily: "var(--font-mono)",
  textTransform: "uppercase",
  letterSpacing: "0.08em",
};

function HeaderCell({ children }: { children: React.ReactNode }) {
  return <div style={headerCellStyle}>{children}</div>;
}

/**
 * Table of all Brand IQ report versions, newest-first.
 * No shadcn table primitive — uses div/grid consistent with the codebase.
 */
export function VersionHistoryTable({ versions }: VersionHistoryTableProps) {
  // Sort newest-first by createdAt (API should already return newest-first,
  // but sort defensively so the UI is always correct)
  const sorted = [...versions].sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
  );

  return (
    <div
      data-testid="version-history-table"
      style={{
        background: "#fff",
        border: "1px solid var(--mly-ink-150)",
        borderRadius: 8,
        overflow: "hidden",
        marginBottom: 18,
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: GRID_COLUMNS,
          gap: 12,
          padding: "8px 16px",
          background: "var(--mly-ink-025)",
          borderBottom: "1px solid var(--mly-ink-150)",
        }}
      >
        <HeaderCell>版本</HeaderCell>
        <HeaderCell>產生時間</HeaderCell>
        <HeaderCell>狀態</HeaderCell>
        <HeaderCell>操作</HeaderCell>
      </div>

      {sorted.map((v, i) => (
        <VersionRow
          key={v.reportId}
          version={v}
          isLast={i === sorted.length - 1}
        />
      ))}
    </div>
  );
}

function VersionRow({
  version,
  isLast,
}: {
  version: ReportVersionItem;
  isLast: boolean;
}) {
  const current = isCurrent(version);
  const downloadHref = `/brand/reports/${version.reportId}/pdf`;

  const formattedDate = version.createdAt
    ? new Date(version.createdAt).toLocaleDateString("zh-TW", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      })
    : "—";

  return (
    <div
      data-testid={`version-row-${version.reportId}`}
      style={{
        display: "grid",
        gridTemplateColumns: GRID_COLUMNS,
        gap: 12,
        padding: "12px 16px",
        alignItems: "center",
        borderBottom: isLast ? "none" : "1px solid var(--mly-ink-100)",
        opacity: current ? 1 : 0.75,
      }}
    >
      {/* Version tag */}
      <div
        style={{
          fontSize: 13,
          fontWeight: 700,
          color: "var(--mly-ink-900)",
          fontFamily: "var(--font-mono)",
        }}
      >
        {version.version}
      </div>

      {/* Date */}
      <div
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: 12,
          color: "var(--mly-ink-500)",
        }}
      >
        {formattedDate}
      </div>

      {/* Status */}
      <div>
        {current ? (
          <span
            data-testid={`status-current-${version.reportId}`}
            style={{
              padding: "2px 8px",
              borderRadius: 999,
              background: "#E0F2F1",
              color: "var(--mly-success)",
              fontSize: 11,
              fontWeight: 700,
            }}
          >
            現行
          </span>
        ) : (
          <span
            data-testid={`status-archived-${version.reportId}`}
            style={{
              padding: "2px 8px",
              borderRadius: 999,
              background: "var(--mly-ink-050)",
              color: "var(--mly-ink-400)",
              fontSize: 11,
              fontFamily: "var(--font-mono)",
            }}
          >
            archived
          </span>
        )}
      </div>

      {/* Actions */}
      <div>
        <a
          href={downloadHref}
          data-testid={`download-version-${version.reportId}`}
          style={{
            background: "transparent",
            color: "var(--mly-ink-700)",
            border: "1px solid var(--mly-ink-200)",
            padding: "5px 10px",
            borderRadius: 5,
            fontSize: 11,
            fontWeight: 600,
            textDecoration: "none",
            display: "inline-flex",
            alignItems: "center",
            gap: 4,
          }}
        >
          <Icon name="download" size={12} color="var(--mly-ink-700)" />
          下載
        </a>
      </div>
    </div>
  );
}
