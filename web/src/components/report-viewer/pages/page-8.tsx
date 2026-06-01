import type { BrandIqReport } from "@/lib/cortex-api";
import { A4Page } from "../shared/a4-page";
import { CertaintyChip } from "../shared/certainty-chip";
import { GridBG } from "../shared/grid-bg";
import { PageFooter } from "../shared/page-footer";
import { PageHeader } from "../shared/page-header";
import { SectionTitle } from "../shared/section-title";

interface Page8Props {
  report: BrandIqReport;
}

/** P8 — 風險 + 來源 + 品質評估 (Light Edition) */
export function Page8({ report }: Page8Props) {
  const b = report.meta;
  const risks = report.risks;
  const sources = report.sources;
  const quality = report.quality;

  // Source-tier tones: A = success (lime-deep), B = brand anchor (teal),
  // C = quiet warm gray. Mirrors the prototype pages-2.jsx P8 block.
  const sourceTiers: Array<{ tier: string; items: string[]; tone: string }> = [
    { tier: "A · 官方來源", items: sources.A, tone: "var(--mly-teal-700)" },
    { tier: "B · 高可信第三方", items: sources.B, tone: "var(--mly-teal-700)" },
    { tier: "C · 未納入主要事實", items: sources.C, tone: "var(--paper-ink-3)" },
  ];

  return (
    <A4Page>
      <GridBG />
      <PageHeader page={8} subject={b.subject} />
      <div style={{ position: "absolute", left: 36, right: 36, top: 76 }}>
        <SectionTitle
          num={8}
          en="Compliance Signals"
          title="合規風險訊號"
          sub="本段為公開資訊風險辨識，不構成法律意見。重要素材建議由合規人員複核。"
        />

        {risks.length === 0 ? (
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
              風險資料尚未建立
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
            {risks.map((r, i) => {
              const high = r.level === "高";
              // Risk surfaces intentionally keep their red/amber signal on
              // the Light Edition (handoff §5: risk colors don't change).
              const surfaceBg = high ? "var(--danger-soft)" : "rgb(244, 249, 250)";
              const surfaceBorder = high
                ? "var(--danger-soft-border)"
                : "var(--mly-teal-200)";
              const adviceTone = high ? "var(--mly-danger)" : "var(--mly-teal-700)";
              // Badge uses the *deep* token of each ramp so #fff text passes
              // WCAG AA. --mly-danger / --gold on their own are too light for
              // white text (~4.0:1 and ~4.1:1 respectively).
              const badgeBg = high ? "var(--danger-deep)" : "var(--mly-teal-700)";
              return (
                <div
                  key={i}
                  style={{
                    padding: 12,
                    background: surfaceBg,
                    border: `1px solid ${surfaceBorder}`,
                    borderRadius: 6,
                  }}
                >
                  <div
                    style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}
                  >
                    <span
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: 9,
                        fontWeight: 700,
                        padding: "2px 6px",
                        background: badgeBg,
                        color: "#fff",
                        borderRadius: 3,
                        letterSpacing: "0.08em",
                      }}
                    >
                      {r.level} 風險
                    </span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: "var(--paper-ink)" }}>
                      {r.theme}
                    </span>
                  </div>
                  <div
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: 10,
                      color: "var(--paper-ink-3)",
                      marginBottom: 4,
                    }}
                  >
                    觸發 · {r.trigger}
                  </div>
                  <div
                    style={{
                      fontSize: 11,
                      color: "var(--paper-ink-2)",
                      lineHeight: 1.55,
                      marginBottom: 6,
                    }}
                  >
                    {r.note}
                  </div>
                  <div
                    style={{
                      paddingTop: 6,
                      borderTop: "1px dashed rgba(100, 120, 130, 0.12)",
                      fontSize: 11,
                      color: "var(--paper-ink)",
                      lineHeight: 1.55,
                    }}
                  >
                    <span
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: 9,
                        letterSpacing: "0.14em",
                        textTransform: "uppercase",
                        color: adviceTone,
                        fontWeight: 700,
                      }}
                    >
                      建議 ·{" "}
                    </span>
                    {r.action}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* sources */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr",
            gap: 10,
            marginBottom: 18,
          }}
        >
          {sourceTiers.map((s) => (
            <div
              key={s.tier}
              style={{
                padding: 12,
                background: "#fff",
                border: "1px solid #d5dee0",
                borderRadius: 6,
              }}
            >
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 9,
                  letterSpacing: "0.14em",
                  textTransform: "uppercase",
                  color: s.tone,
                  fontWeight: 700,
                  marginBottom: 8,
                }}
              >
                {s.tier}
              </div>
              {s.items.length === 0 ? (
                <CertaintyChip value="資料不足" />
              ) : (
                <ul
                  style={{
                    margin: 0,
                    padding: 0,
                    listStyle: "none",
                    display: "grid",
                    gap: 4,
                  }}
                >
                  {s.items.map((src, j) => (
                    <li
                      key={j}
                      style={{
                        fontSize: 10.5,
                        color: "var(--paper-ink-2)",
                        display: "grid",
                        gridTemplateColumns: "8px 1fr",
                        gap: 6,
                        lineHeight: 1.55,
                      }}
                    >
                      <span style={{ color: s.tone, marginTop: 6 }}>·</span>
                      <span>{src}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>

        {/* data quality */}
        <SectionTitle num={10} en="Data Quality" title="資料品質評估" />
        <div
          style={{
            border: "1px solid #d5dee0",
            borderRadius: 6,
            overflow: "hidden",
            background: "#fff",
          }}
        >
          {[
            { l: "高信心段落", v: quality.high, tone: "var(--mly-teal-700)" },
            { l: "中低信心段落", v: quality.midLow, tone: "var(--mly-teal-400)" },
            { l: "已知缺口", v: quality.gaps, tone: "var(--paper-ink-3)" },
            { l: "來源衝突", v: quality.conflicts, tone: "var(--paper-ink-3)" },
            { l: "不足以確認", v: quality.open, tone: "var(--paper-ink-3)" },
          ].map((r, i, a) => (
            <div
              key={r.l}
              style={{
                display: "grid",
                gridTemplateColumns: "140px 1fr",
                padding: "9px 14px",
                gap: 14,
                borderBottom:
                  i < a.length - 1 ? "1px solid #d5dee0" : "none",
                fontSize: 11.5,
                lineHeight: 1.55,
                background: i % 2 === 0 ? "transparent" : "#f5f5f5",
              }}
            >
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 10,
                  letterSpacing: "0.06em",
                  color: r.tone,
                  fontWeight: 700,
                  textTransform: "uppercase",
                }}
              >
                {r.l}
              </div>
              <div style={{ color: "var(--paper-ink-2)" }}>
                {r.v || <CertaintyChip value="資料不足" />}
              </div>
            </div>
          ))}
        </div>
      </div>

      <PageFooter page={8} pageCount={b.pageCount} />
    </A4Page>
  );
}
