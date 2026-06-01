"use client";

import type { ReportVersionItem } from "@/lib/cortex-api";
import { Icon } from "@/components/report-viewer/shared/icon";
import { FeaturedReportCard } from "./featured-report-card";
import { VersionHistoryTable } from "./version-history-table";
import { OtherResources } from "./other-resources";
import { isCurrent } from "./is-current";

interface KnowledgeBasePageProps {
  versions: ReportVersionItem[];
}

/**
 * Knowledge Base page — permanent library entry for a brand's Cortex assets.
 *
 * Shows Brand Reports (current + history), and pending placeholder sections
 * for product knowledge cards, brand voice samples, competitor notes, and the
 * weekly report template. Non-report resources have NO API yet and are clearly
 * marked "準備中" with no invented counts.
 */
export function KnowledgeBasePage({ versions }: KnowledgeBasePageProps) {
  const currentVersion = versions.find(isCurrent);
  const hasReports = versions.length > 0;

  return (
    <div
      data-testid="knowledge-base-page"
      style={{ padding: "24px 32px 48px", background: "#fff", minHeight: "100vh" }}
    >
      {/* Breadcrumb */}
      <div
        style={{
          display: "flex",
          alignItems: "baseline",
          gap: 12,
          marginBottom: 24,
        }}
      >
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 11,
            color: "var(--mly-ink-500)",
            letterSpacing: "0.14em",
            textTransform: "uppercase",
          }}
        >
          BRAND CORTEX
        </div>
      </div>

      {/* Title + description */}
      <h1
        style={{
          fontSize: 28,
          fontWeight: 700,
          color: "var(--mly-ink-900)",
          letterSpacing: "-0.02em",
          marginBottom: 6,
          fontFamily: "var(--font-sans)",
        }}
      >
        Knowledge Base
      </h1>
      <div
        style={{ fontSize: 13, color: "var(--mly-ink-500)", marginBottom: 20 }}
      >
        所有 Cortex 為你的品牌整理的素材都保存在這裡——可隨時下載、版本化、與團隊分享。
      </div>

      {/* Section header — "Brand Reports" is the only live category this
          slice. The others are not interactive (no API yet), so they are
          rendered as honest dimmed "coming soon" labels rather than fake
          tabs with misleading tab ARIA. */}
      <div
        data-testid="kb-section-header"
        style={{
          display: "flex",
          alignItems: "baseline",
          gap: 16,
          flexWrap: "wrap",
          borderBottom: "1px solid var(--mly-ink-150)",
          paddingBottom: 12,
          marginBottom: 20,
        }}
      >
        <div
          style={{
            fontSize: 15,
            fontWeight: 700,
            color: "var(--mly-teal-700)",
          }}
        >
          Brand Reports
        </div>
        {["所有檔案", "產品知識卡", "Brand Voice 樣本", "競品筆記"].map((label) => (
          <span
            key={label}
            style={{
              fontSize: 13,
              fontWeight: 500,
              color: "var(--mly-ink-300)",
              userSelect: "none",
            }}
          >
            {label}
            <span
              style={{
                marginLeft: 4,
                fontSize: 10,
                fontFamily: "var(--font-mono)",
                fontStyle: "italic",
                color: "var(--mly-ink-400)",
              }}
            >
              準備中
            </span>
          </span>
        ))}
      </div>

      {/* Main content */}
      {!hasReports ? (
        <EmptyState />
      ) : (
        <>
          {/* Featured card — current version */}
          {currentVersion && (
            <FeaturedReportCard version={currentVersion} />
          )}

          {/* Version history */}
          <div
            style={{
              fontSize: 14,
              fontWeight: 700,
              color: "var(--mly-ink-900)",
              margin: "16px 0 8px",
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            歷史版本
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 11,
                color: "var(--mly-ink-500)",
                fontWeight: 500,
              }}
            >
              · 每次重大設定變動，Cortex 都會自動歸檔
            </span>
          </div>
          <VersionHistoryTable versions={versions} />

          {/* Other resources */}
          <div
            style={{
              fontSize: 14,
              fontWeight: 700,
              color: "var(--mly-ink-900)",
              margin: "20px 0 8px",
            }}
          >
            其他知識資源
          </div>
          <OtherResources />

          {/* Info panel */}
          <div
            style={{
              marginTop: 20,
              padding: "14px 16px",
              background: "var(--mly-ink-025)",
              border: "1px dashed var(--mly-ink-200)",
              borderRadius: 8,
              display: "flex",
              alignItems: "flex-start",
              gap: 10,
            }}
          >
            <Icon
              name="info"
              size={16}
              color="var(--mly-ink-500)"
              style={{ flexShrink: 0, marginTop: 1 }}
            />
            <span style={{ fontSize: 12, color: "var(--mly-ink-600)" }}>
              Brand IQ 報告是 onboarding 抓取資料的快照。日常營運訊號請在 Discover 查看，或下載每週的
              Performance Report。
            </span>
          </div>
        </>
      )}
    </div>
  );
}

// ─── Empty state ──────────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <div
      data-testid="empty-state"
      style={{
        minHeight: "40vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 12,
        padding: "48px 24px",
        textAlign: "center",
      }}
    >
      {/* Icon illustration */}
      <div
        style={{
          width: 56,
          height: 56,
          borderRadius: 12,
          background: "var(--mly-teal-050)",
          display: "grid",
          placeItems: "center",
          marginBottom: 4,
        }}
      >
        <Icon name="auto_stories" size={28} color="var(--mly-teal-400)" />
      </div>

      <div
        style={{
          fontSize: 17,
          fontWeight: 700,
          color: "var(--mly-ink-800)",
          fontFamily: "var(--font-sans)",
        }}
      >
        尚無 Brand IQ 報告
      </div>
      <div
        style={{
          fontSize: 13,
          color: "var(--mly-ink-500)",
          maxWidth: 400,
          lineHeight: 1.6,
        }}
      >
        完成 onboarding 後，Cortex 將自動生成你的第一份 Brand IQ 報告。報告就緒後會顯示在這裡。
      </div>
    </div>
  );
}
