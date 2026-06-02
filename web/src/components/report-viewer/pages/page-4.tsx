import type { BrandIqReport } from "@/lib/cortex-api";
import { A4Page } from "../shared/a4-page";
import { CertaintyChip } from "../shared/certainty-chip";
import { ConstellationSVG } from "../shared/constellation-svg";
import { GridBG } from "../shared/grid-bg";
import { Icon } from "../shared/icon";
import { PageFooter } from "../shared/page-footer";
import { PageHeader } from "../shared/page-header";
import { SectionTitle } from "../shared/section-title";

interface Page4Props {
  report: BrandIqReport;
}

/** P4 — 媒體網絡 · The Reachable Galaxy (Light Edition) */
export function Page4({ report }: Page4Props) {
  const b = report.meta;
  const media = report.mediaNetwork;

  return (
    <A4Page>
      <GridBG />
      <PageHeader page={4} subject={b.subject} />
      <div style={{ position: "absolute", left: 36, right: 36, top: 70 }}>
        <SectionTitle
          num={3}
          en="Media Network"
          title="你的品牌能被聽見的地方"
          sub={`Cortex onboarding 階段選定 ${media.length} 家媒體做 Context Agent 部署。`}
        />
      </div>


      <div style={{ position: "absolute", left: 36, right: 36, top: 160 }}>
        {media.length === 0 ? (
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
              媒體網絡資料尚未建立
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
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1.5fr 1.5fr 0.6fr 1.4fr 0.6fr 0.4fr",
                padding: "10px 14px",
                fontFamily: "var(--font-mono)",
                fontSize: 9,
                letterSpacing: "0.14em",
                textTransform: "uppercase",
                color: "var(--paper-ink-3)",
                borderBottom: "1px solid #d5dee0",
                background: "#f5f5f5",
                fontWeight: 700,
              }}
            >
              <span>媒體</span>
              <span>讀者輪廓</span>
              <span style={{ textAlign: "right" }}>週讀者</span>
              <span>主題</span>
              <span style={{ textAlign: "right" }}>相關性</span>
              <span style={{ textAlign: "right" }}>趨勢</span>
            </div>
            {media.map((m, i) => {
              const trendIcon =
                m.trend === "上升"
                  ? "trending_up"
                  : m.trend === "下降"
                    ? "trending_down"
                    : "trending_flat";
              const trendColor =
                m.trend === "上升"
                  ? "var(--mly-teal-700)"
                  : m.trend === "下降"
                    ? "var(--mly-danger)"
                    : "var(--paper-ink-3)";
              return (
                <div
                  key={m.name}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1.5fr 1.5fr 0.6fr 1.4fr 0.6fr 0.4fr",
                    padding: "11px 14px",
                    fontSize: 11.5,
                    color: "var(--paper-ink-2)",
                    borderBottom:
                      i < media.length - 1
                        ? "1px solid #d5dee0"
                        : "none",
                    alignItems: "center",
                    background: i % 2 === 0 ? "transparent" : "#f5f5f5",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      fontWeight: 700,
                      color: "var(--paper-ink)",
                    }}
                  >
                    <span
                      style={{
                        width: 7,
                        height: 7,
                        borderRadius: "50%",
                        background: "var(--mly-teal-700)",
                        boxShadow: "0 0 6px rgba(28, 114, 107, 0.40)",
                        flexShrink: 0,
                      }}
                    />
                    {m.name}
                  </div>
                  <div style={{ color: "var(--paper-ink-3)" }}>{m.audience}</div>
                  <div
                    style={{
                      textAlign: "right",
                      fontFamily: "var(--font-numeric)",
                      fontWeight: 700,
                      color: "var(--paper-ink)",
                    }}
                  >
                    {m.weekly}
                  </div>
                  <div style={{ color: "var(--paper-ink-3)", fontSize: 11 }}>
                    {m.topics}
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <span
                      style={{
                        fontFamily: "var(--font-numeric)",
                        fontSize: 13,
                        fontWeight: 700,
                        color:
                          m.relevance >= 90
                            ? "var(--mly-teal-700)"
                            : m.relevance >= 80
                              ? "var(--mly-teal-700)"
                              : "var(--paper-ink-3)",
                      }}
                    >
                      {m.relevance}
                    </span>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <Icon name={trendIcon} size={14} color={trendColor} />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <PageFooter page={4} pageCount={b.pageCount} />
    </A4Page>
  );
}
