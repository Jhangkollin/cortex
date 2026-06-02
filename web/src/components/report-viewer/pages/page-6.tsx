import type { BrandIqReport } from "@/lib/cortex-api";
import { A4Page } from "../shared/a4-page";
import { CertaintyChip } from "../shared/certainty-chip";
import { GridBG } from "../shared/grid-bg";
import { PageFooter } from "../shared/page-footer";
import { PageHeader } from "../shared/page-header";
import { SectionTitle } from "../shared/section-title";

interface Page6Props {
  report: BrandIqReport;
}

/** P6 — 戰略洞察 · Strategic Insights (Light Edition) */
export function Page6({ report }: Page6Props) {
  const b = report.meta;
  const insights = report.insights;

  // Light Edition: each evidence tier gets its own paper-tile surface in the
  // brand palette — lime-soft for confirmed facts, teal-soft for inferences,
  // gold-soft for hypotheses. Mirrors the prototype pages-2.jsx P6 block.
  const cols: Array<{
    h: string;
    en: string;
    items: string[];
    tone: string;
    bg: string;
    border: string;
  }> = [
    {
      h: "已確認事實",
      en: "Confirmed",
      items: insights.confirmed,
      tone: "var(--mly-teal-700)",
      bg: "rgb(244, 249, 250)",
      border: "var(--mly-teal-200)",
    },
    {
      h: "合理推論",
      en: "Inferences",
      items: insights.inferences,
      tone: "var(--mly-teal-700)",
      bg: "rgb(244, 249, 250)",
      border: "var(--mly-teal-200)",
    },
    {
      h: "待驗證假設",
      en: "Hypotheses",
      items: insights.hypotheses,
      tone: "var(--mly-teal-700)",
      bg: "rgb(244, 249, 250)",
      border: "var(--mly-teal-200)",
    },
  ];

  return (
    <A4Page>
      <GridBG />
      <PageHeader page={6} subject={b.subject} />
      <div style={{ position: "absolute", left: 36, right: 36, top: 76 }}>
        <SectionTitle
          num={5}
          en="Strategic Insights"
          title="從訊號到行動"
          sub="按證據強度分層：已確認事實 → 合理推論 → 待驗證假設。每一層的決策重量不同。"
        />

        <div style={{ display: "grid", gap: 12 }}>
          {cols.map((c, i) => (
            <div
              key={c.h}
              style={{
                padding: 16,
                borderRadius: 8,
                background: c.bg,
                border: `1px solid ${c.border}`,
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  marginBottom: 8,
                }}
              >
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 15,
                    letterSpacing: "0.08em",
                    textTransform: "uppercase",
                    color: c.tone,
                    fontWeight: 700,
                  }}
                >
                  0{i + 1} · {c.en}
                </span>
                <span style={{ fontSize: 15, fontWeight: 700, color: "var(--paper-ink)" }}>
                  {c.h}
                </span>
              </div>
              {c.items.length === 0 ? (
                <div style={{ paddingLeft: 4 }}>
                  <CertaintyChip value="資料不足" />
                </div>
              ) : (
                <ol
                  style={{ margin: 0, padding: "0 0 0 16px", listStyle: "none", display: "grid", gap: 6 }}
                >
                  {c.items.map((t, idx) => (
                    <li
                      key={idx}
                      style={{
                        display: "grid",
                        gridTemplateColumns: "auto 1fr",
                        gap: 10,
                        alignItems: "flex-start",
                        fontSize: 12.5,
                        color: "var(--paper-ink)",
                        lineHeight: 1.65,
                      }}
                    >
                      <span
                        style={{
                          fontFamily: "var(--font-mono)",
                          fontSize: 10,
                          color: c.tone,
                          fontWeight: 700,
                          marginTop: 2,
                        }}
                      >
                        {String(idx + 1).padStart(2, "0")}
                      </span>
                      <span>{t}</span>
                    </li>
                  ))}
                </ol>
              )}
            </div>
          ))}
        </div>
      </div>

      <PageFooter page={6} pageCount={b.pageCount} />
    </A4Page>
  );
}
