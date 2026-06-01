import type { BrandIqReport } from "@/lib/cortex-api";
import { A4Page } from "../shared/a4-page";
import { CertaintyChip } from "../shared/certainty-chip";
import { GridBG } from "../shared/grid-bg";
import { Icon } from "../shared/icon";
import { PageFooter } from "../shared/page-footer";
import { PageHeader } from "../shared/page-header";
import { SectionTitle } from "../shared/section-title";

interface Page3Props {
  report: BrandIqReport;
}

/** P3 — 產品線結構 · Portfolio (Light Edition) */
export function Page3({ report }: Page3Props) {
  const b = report.meta;
  const lines = report.productLines;
  const subBrands = report.subBrands;

  return (
    <A4Page>
      <GridBG />
      <PageHeader page={3} subject={b.subject} />
      <div style={{ position: "absolute", left: 36, right: 36, top: 76 }}>
        <SectionTitle
          num={2}
          en="Product Portfolio"
          title={`${lines.length} 條產品線`}
          sub="官方網站抓取產品頁面，按產品線級別整理。信心值低的線別建議向客戶確認。"
        />

        {lines.length === 0 ? (
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
              產品線資料尚未建立
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
                gridTemplateColumns: "1.0fr 1.4fr 1.5fr 1.5fr 0.5fr",
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
              <span>線別</span>
              <span>核心訴求</span>
              <span>代表性產品</span>
              <span>差異化訊號</span>
              <span style={{ textAlign: "right" }}>信心</span>
            </div>
            {lines.map((p, i) => (
              <div
                key={p.line}
                style={{
                  display: "grid",
                  gridTemplateColumns: "1.0fr 1.4fr 1.5fr 1.5fr 0.5fr",
                  padding: "11px 14px",
                  fontSize: 11.5,
                  color: "var(--paper-ink-2)",
                  lineHeight: 1.5,
                  borderBottom:
                    i < lines.length - 1
                      ? "1px solid #d5dee0"
                      : "none",
                  alignItems: "center",
                  background: i % 2 === 0 ? "transparent" : "#f5f5f5",
                }}
              >
                <div style={{ fontWeight: 700, color: "var(--paper-ink)" }}>{p.line}</div>
                <div>{p.thesis}</div>
                <div
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 10.5,
                    color: "var(--paper-ink)",
                  }}
                >
                  {p.examples}
                </div>
                <div style={{ color: "var(--paper-ink-3)", fontSize: 11 }}>
                  {p.signal}
                </div>
                <div
                  style={{
                    textAlign: "right",
                    fontFamily: "var(--font-numeric)",
                    fontWeight: 700,
                    fontSize: 13,
                    color:
                      p.confidence >= 90
                        ? "var(--mly-teal-700)"
                        : p.confidence >= 80
                          ? "var(--mly-teal-700)"
                          : "var(--mly-teal-400)",
                  }}
                >
                  {p.confidence}%
                </div>
              </div>
            ))}
          </div>
        )}

        {report.productNote ? (
          <div
            style={{
              marginTop: 14,
              padding: "10px 14px",
              background: "rgb(244, 249, 250)",
              border: "1px solid var(--mly-teal-200)",
              borderRadius: 6,
              fontSize: 11.5,
              color: "var(--mly-teal-700)",
              display: "flex",
              gap: 10,
              alignItems: "flex-start",
            }}
          >
            <Icon name="info" size={14} color="var(--mly-teal-400)" />
            <span>{report.productNote}</span>
          </div>
        ) : null}

        {/* sub-brands */}
        <div style={{ marginTop: 22 }}>
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 10,
              letterSpacing: "0.2em",
              textTransform: "uppercase",
              color: "var(--mly-teal-400)",
              fontWeight: 700,
              marginBottom: 8,
            }}
          >
            子品牌 / 系列 · Sub-brands
          </div>
          {subBrands.length === 0 ? (
            <div
              style={{
                padding: 12,
                background: "#fff",
                border: "1px solid #d5dee0",
                borderRadius: 6,
              }}
            >
              <CertaintyChip value="資料不足" />
            </div>
          ) : (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, 1fr)",
                gap: 10,
              }}
            >
              {subBrands.map((s) => (
                <div
                  key={s.type}
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
                      color: "var(--paper-ink-3)",
                      marginBottom: 4,
                    }}
                  >
                    {s.type}
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: "var(--paper-ink)" }}>
                    {s.name}
                  </div>
                  <div
                    style={{
                      fontSize: 11,
                      color: "var(--paper-ink-3)",
                      marginTop: 6,
                      lineHeight: 1.5,
                    }}
                  >
                    {s.note}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* endorsements / IP collabs */}
        <div
          style={{
            marginTop: 14,
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 10,
          }}
        >
          {[
            { h: "代言人 / 名人合作", v: report.endorsements },
            { h: "IP 聯名", v: report.ipCollabs },
          ].map((block) => (
            <div
              key={block.h}
              style={{
                padding: 12,
                background: "#f5f5f5",
                border: "1px dashed #d5dee0",
                borderRadius: 6,
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  marginBottom: 4,
                }}
              >
                <span style={{ fontSize: 12, fontWeight: 700, color: "var(--paper-ink)" }}>
                  {block.h}
                </span>
                <CertaintyChip value={block.v.status} />
              </div>
              <div
                style={{
                  fontSize: 11,
                  color: "var(--paper-ink-3)",
                  lineHeight: 1.5,
                }}
              >
                {block.v.body}
              </div>
            </div>
          ))}
        </div>
      </div>

      <PageFooter page={3} pageCount={b.pageCount} />
    </A4Page>
  );
}
