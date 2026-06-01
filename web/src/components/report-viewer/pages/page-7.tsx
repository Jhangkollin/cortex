import type { BrandIqReport } from "@/lib/cortex-api";
import { A4Page } from "../shared/a4-page";
import { CertaintyChip } from "../shared/certainty-chip";
import { GridBG } from "../shared/grid-bg";
import { PageFooter } from "../shared/page-footer";
import { PageHeader } from "../shared/page-header";
import { SectionTitle } from "../shared/section-title";

interface Page7Props {
  report: BrandIqReport;
}

/** P7 — 讀者熱問 + 通路布局 (Light Edition) */
export function Page7({ report }: Page7Props) {
  const b = report.meta;
  const faq = report.faq;
  const channels = report.channels;

  return (
    <A4Page>
      <GridBG />
      <PageHeader page={7} subject={b.subject} />
      <div style={{ position: "absolute", left: 36, right: 36, top: 76 }}>
        <SectionTitle
          num={6}
          en="Reader FAQ"
          title="讀者最常問的問題"
          sub={`從 onboarding 階段抓取的 ${faq.length} 大高強度問題，Cortex 預先準備了符合品牌語氣的回應。`}
        />

        {faq.length === 0 ? (
          <div
            style={{
              padding: 18,
              background: "#fff",
              border: "1px solid #d5dee0",
              borderRadius: 8,
              marginBottom: 22,
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <CertaintyChip value="資料不足" />
            <span style={{ fontSize: 12, color: "var(--paper-ink-2)" }}>
              讀者問題資料尚未建立
            </span>
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 10,
              marginBottom: 22,
            }}
          >
            {faq.map((row, i) => (
              <div
                key={i}
                style={{
                  padding: 12,
                  background: "#fff",
                  border: "1px solid #d5dee0",
                  borderRadius: 6,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: 6,
                    marginBottom: 6,
                  }}
                >
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: 9,
                      color: "var(--mly-teal-400)",
                      fontWeight: 700,
                      marginTop: 1,
                    }}
                  >
                    Q{i + 1}
                  </span>
                  <div
                    style={{
                      fontSize: 12,
                      fontWeight: 700,
                      color: "var(--paper-ink)",
                      lineHeight: 1.5,
                    }}
                  >
                    {row.q}
                  </div>
                </div>
                <div
                  style={{
                    fontSize: 10.5,
                    color: "var(--paper-ink-2)",
                    lineHeight: 1.6,
                  }}
                >
                  {row.a}
                </div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    marginTop: 8,
                    paddingTop: 6,
                    borderTop: "1px dashed #d5dee0",
                  }}
                >
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: 9,
                      color: "var(--paper-ink-3)",
                    }}
                  >
                    {row.source}
                  </span>
                  <span
                    style={{
                      marginLeft: "auto",
                      fontFamily: "var(--font-mono)",
                      fontSize: 9,
                      padding: "1px 6px",
                      background: "rgb(244, 249, 250)",
                      color: "var(--mly-teal-700)",
                      borderRadius: 3,
                      fontWeight: 700,
                      border: "1px solid var(--mly-teal-200)",
                    }}
                  >
                    {row.level}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        <SectionTitle
          num={7}
          en="Channels"
          title="通路布局"
          sub="D2C、媒體網絡、實體與海外通路的當前覆蓋。"
        />

        {channels.length === 0 ? (
          <div
            style={{
              padding: 18,
              background: "#fff",
              border: "1px solid #d5dee0",
              borderRadius: 8,
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <CertaintyChip value="資料不足" />
            <span style={{ fontSize: 12, color: "var(--paper-ink-2)" }}>
              通路資料尚未建立
            </span>
          </div>
        ) : (
          <div
            style={{
              border: "1px solid #d5dee0",
              borderRadius: 8,
              overflow: "hidden",
              background: "#fff",
            }}
          >
            {channels.map((ch, i) => (
              <div
                key={ch.type}
                style={{
                  display: "grid",
                  gridTemplateColumns: "180px 1.4fr 1.4fr",
                  padding: "11px 14px",
                  fontSize: 11.5,
                  color: "var(--paper-ink-2)",
                  alignItems: "flex-start",
                  borderBottom:
                    i < channels.length - 1
                      ? "1px solid #d5dee0"
                      : "none",
                  background: i % 2 === 0 ? "transparent" : "#f5f5f5",
                }}
              >
                <div style={{ fontWeight: 700, color: "var(--paper-ink)" }}>{ch.type}</div>
                <div style={{ color: "var(--paper-ink-2)", paddingRight: 12 }}>
                  {ch.surfaces === "資料不足" ? (
                    <CertaintyChip value="資料不足" />
                  ) : (
                    ch.surfaces
                  )}
                </div>
                <div
                  style={{
                    color: "var(--paper-ink-3)",
                    fontSize: 11,
                    lineHeight: 1.5,
                  }}
                >
                  {ch.read}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <PageFooter page={7} pageCount={b.pageCount} />
    </A4Page>
  );
}
