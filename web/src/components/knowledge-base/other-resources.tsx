"use client";

import { Icon } from "@/components/report-viewer/shared/icon";

/**
 * Pending placeholder rows for KB resource types that have no API yet.
 *
 * CRITICAL HONESTY: These rows show NO counts and NO data — only a clear
 * "準備中" (pending) state. The prototype's "6 張 / 4 句" are demo fixtures
 * that MUST NOT be reproduced here.
 */
export function OtherResources() {
  const rows: Array<{
    icon: string;
    label: string;
    description: string;
    testId: string;
  }> = [
    {
      icon: "category",
      label: "產品知識卡",
      description: "Cortex 從品牌網站擷取的結構化產品知識，未來可用於 AI 代理回答與媒體比對。",
      testId: "resource-product-cards",
    },
    {
      icon: "campaign",
      label: "Brand Voice 樣本",
      description: "從官方頁面萃取的語調樣本，用於校準 AI 產出符合品牌聲音。",
      testId: "resource-brand-voice",
    },
    {
      icon: "groups",
      label: "競品筆記",
      description: "競品定位、通路重疊與品類監測的摘要，每次報告更新時自動刷新。",
      testId: "resource-competitor-notes",
    },
    {
      icon: "schedule",
      label: "週報模板",
      description: "Cortex 將每週自動匯整品牌表現與下週行動建議，首份將在完成 onboarding 後七天內生成。",
      testId: "resource-weekly-report",
    },
  ];

  return (
    <div
      data-testid="other-resources"
      style={{
        background: "#fff",
        border: "1px solid var(--mly-ink-150)",
        borderRadius: 8,
        overflow: "hidden",
      }}
    >
      {rows.map((row, i) => (
        <div
          key={row.testId}
          data-testid={row.testId}
          style={{
            display: "grid",
            gridTemplateColumns: "32px 1fr 100px",
            gap: 12,
            padding: "12px 16px",
            alignItems: "center",
            borderBottom: i < rows.length - 1 ? "1px solid var(--mly-ink-100)" : "none",
            opacity: 0.75,
          }}
        >
          {/* Icon */}
          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: 6,
              background: "var(--mly-teal-050)",
              display: "grid",
              placeItems: "center",
              flexShrink: 0,
            }}
          >
            <Icon name={row.icon} size={14} color="var(--mly-teal-700)" />
          </div>

          {/* Label + description */}
          <div>
            <div
              style={{ fontSize: 13, fontWeight: 600, color: "var(--mly-ink-900)" }}
            >
              {row.label}
            </div>
            <div
              style={{ fontSize: 11, color: "var(--mly-ink-500)", marginTop: 2 }}
            >
              {row.description}
            </div>
          </div>

          {/* Pending badge — no action available yet */}
          <div>
            <span
              data-testid={`${row.testId}-pending`}
              style={{
                fontSize: 10,
                color: "var(--mly-ink-400)",
                fontFamily: "var(--font-mono)",
                fontStyle: "italic",
                whiteSpace: "nowrap",
              }}
            >
              準備中
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
