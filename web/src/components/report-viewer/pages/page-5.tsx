import type { BrandIqReport } from "@/lib/cortex-api";
import { A4Page } from "../shared/a4-page";
import { CertaintyChip } from "../shared/certainty-chip";
import { GridBG } from "../shared/grid-bg";
import { Icon } from "../shared/icon";
import { PageFooter } from "../shared/page-footer";
import { PageHeader } from "../shared/page-header";
import { SectionTitle } from "../shared/section-title";

interface Page5Props {
  report: BrandIqReport;
}

/** P5 — 競品輪廓 · Competitor Landscape (Light Edition) */
export function Page5({ report }: Page5Props) {
  const b = report.meta;
  const competitors = report.competitors;

  // Tier 0 (direct) keeps a red signal even after the dark→light flip — see
  // --danger-soft/--danger-soft-border in globals.css; tier 1 (monitoring)
  // uses the gold ceremony surface; tier 2 (substitute) sits on the neutral
  // warm-cream baseline.
  const tones = [
    {
      color: "var(--mly-danger)",
      soft: "var(--danger-soft)",
      border: "var(--danger-soft-border)",
    },
    {
      color: "var(--mly-teal-400)",
      soft: "rgb(244, 249, 250)",
      border: "var(--mly-teal-200)",
    },
    {
      color: "var(--paper-ink-3)",
      soft: "#f5f5f5",
      border: "#d5dee0",
    },
  ];

  return (
    <A4Page>
      <GridBG />
      <PageHeader page={5} subject={b.subject} />
      <div style={{ position: "absolute", left: 36, right: 36, top: 76 }}>
        <SectionTitle
          num={4}
          en="Competitive Position"
          title="你在這個品類的位置"
          sub="三層次競品分析：直接競爭、監測中、替代型。判斷基於品類重疊、通路重疊與品牌化程度。"
        />

        {competitors.length === 0 ? (
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
              競品資料尚未建立
            </span>
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr",
              gap: 10,
            }}
          >
            {competitors.map((c, i) => {
              const tone = tones[i] ?? tones[2]!;
              return (
                <div
                  key={c.tier}
                  style={{
                    padding: 14,
                    background: "#fff",
                    border: "1px solid #d5dee0",
                    borderRadius: 8,
                    borderTop: `3px solid ${tone.color}`,
                    boxShadow: "0 1px 2px rgba(var(--paper-ink-rgb), 0.04)",
                  }}
                >
                  <span
                    style={{
                      display: "inline-block",
                      padding: "3px 8px",
                      borderRadius: 999,
                      background: tone.soft,
                      color: tone.color,
                      fontSize: 10,
                      fontFamily: "var(--font-mono)",
                      fontWeight: 700,
                      letterSpacing: "0.08em",
                      marginBottom: 8,
                      border: `1px solid ${tone.border}`,
                    }}
                  >
                    {c.tier}
                  </span>
                  <div
                    style={{
                      fontSize: 14,
                      fontWeight: 700,
                      color: "var(--paper-ink)",
                      lineHeight: 1.35,
                    }}
                  >
                    {c.brands}
                  </div>
                  <div
                    style={{
                      fontSize: 11.5,
                      color: "var(--paper-ink-2)",
                      marginTop: 10,
                      lineHeight: 1.6,
                    }}
                  >
                    {c.basis}
                  </div>
                  <div
                    style={{
                      marginTop: 10,
                      paddingTop: 10,
                      borderTop: "1px dashed #d5dee0",
                    }}
                  >
                    <div
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: 9,
                        letterSpacing: "0.14em",
                        textTransform: "uppercase",
                        color: "var(--paper-ink-3)",
                        marginBottom: 4,
                        fontWeight: 700,
                      }}
                    >
                      相對位置
                    </div>
                    <div
                      style={{
                        fontSize: 11.5,
                        color: "var(--paper-ink)",
                        lineHeight: 1.55,
                      }}
                    >
                      {c.position}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {report.competitorNote ? (
          <div
            style={{
              marginTop: 14,
              padding: "10px 14px",
              background: "#fff",
              border: "1px solid #d5dee0",
              borderRadius: 6,
              fontSize: 11,
              color: "var(--paper-ink-3)",
              display: "flex",
              gap: 8,
              alignItems: "flex-start",
            }}
          >
            <Icon name="psychology" size={13} color="var(--mly-teal-700)" />
            <span>
              <strong style={{ color: "var(--paper-ink)" }}>分析師備註：</strong>
              {report.competitorNote}
            </span>
          </div>
        ) : null}
      </div>

      <PageFooter page={5} pageCount={b.pageCount} />
    </A4Page>
  );
}
