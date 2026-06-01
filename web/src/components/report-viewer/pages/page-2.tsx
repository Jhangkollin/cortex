import type { BrandIqReport } from "@/lib/cortex-api";
import { A4Page } from "../shared/a4-page";
import { CertaintyChip } from "../shared/certainty-chip";
import { GridBG } from "../shared/grid-bg";
import { PageFooter } from "../shared/page-footer";
import { PageHeader } from "../shared/page-header";
import { SectionTitle } from "../shared/section-title";

/**
 * NOTE: the "white card on paper" shell (padding + #fff bg +
 * #d5dee0 border) is repeated across page-2..page-8.
 * Intentionally NOT extracted to a shared <PaperCard /> in this slice —
 * individual pages add per-section variants (top-border tone strips on
 * page-5, optional shadow on page-3 certainty cards, etc.). If a future
 * design revision unifies the card surface, extract then.
 */
interface Page2Props {
  report: BrandIqReport;
}

/** P2 — 品牌核心 · The Anatomy (Light Edition) */
export function Page2({ report }: Page2Props) {
  const b = report.meta;
  const core = report.core.length > 0 ? report.core : [];
  const showEmpty = core.length === 0;

  return (
    <A4Page>
      <GridBG />
      <PageHeader page={2} subject={b.subject} />

      <div style={{ position: "absolute", left: 36, right: 36, top: 76 }}>
        <SectionTitle
          num={1}
          en="Brand Anatomy"
          title="品牌核心解剖"
          sub={`從公開資料整理 ${b.subject} 的品牌主體、市場、定位與研發敘事。`}
        />

        {showEmpty ? (
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
              品牌核心資料尚未建立
            </span>
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 10,
              marginTop: 6,
            }}
          >
            {core.map((row, i) => (
              <div
                key={i}
                style={{
                  padding: 14,
                  background: "#fff",
                  border: "1px solid #d5dee0",
                  borderRadius: 8,
                  boxShadow: "0 1px 2px rgba(var(--paper-ink-rgb), 0.04)",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    marginBottom: 6,
                  }}
                >
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: 9,
                      color: "var(--mly-teal-400)",
                      fontWeight: 700,
                    }}
                  >
                    0{i + 1}
                  </span>
                  <span style={{ fontSize: 13, fontWeight: 700, color: "var(--paper-ink)" }}>
                    {row.item}
                  </span>
                  <span style={{ marginLeft: "auto" }}>
                    <CertaintyChip value={row.certainty} />
                  </span>
                </div>
                <div
                  style={{ fontSize: 11.5, color: "var(--paper-ink-2)", lineHeight: 1.65 }}
                >
                  {row.body}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* judgement pull quote — gold-soft tile with deep-gold accent rail */}
        <div
          style={{
            marginTop: 18,
            padding: "16px 18px",
            background: "rgb(244, 249, 250)",
            border: "1px solid var(--mly-teal-200)",
            borderLeft: "3px solid var(--mly-teal-400)",
            borderRadius: 6,
            display: "grid",
            gridTemplateColumns: "auto 1fr",
            gap: 14,
            alignItems: "flex-start",
          }}
        >
          <div
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: 36,
              fontStyle: "italic",
              color: "var(--mly-teal-400)",
              lineHeight: 1,
              fontWeight: 700,
              marginTop: -2,
            }}
          >
            &ldquo;
          </div>
          <div>
            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 9,
                letterSpacing: "0.18em",
                textTransform: "uppercase",
                color: "var(--mly-teal-700)",
                marginBottom: 6,
                fontWeight: 700,
              }}
            >
              Cortex 的判斷
            </div>
            <div
              style={{
                fontFamily: "var(--font-serif-tc)",
                fontSize: 15,
                color: "var(--paper-ink)",
                lineHeight: 1.65,
                fontStyle: "italic",
              }}
            >
              {report.coreJudgement || <CertaintyChip value="資料不足" />}
            </div>
          </div>
        </div>

        {/* at-a-glance stats */}
        <div style={{ marginTop: 18 }}>
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 10,
              letterSpacing: "0.2em",
              textTransform: "uppercase",
              color: "var(--paper-ink-3)",
              marginBottom: 8,
              fontWeight: 700,
            }}
          >
            At a glance
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: 10,
            }}
          >
            {[
              { l: "成立", v: b.founded ?? "—", sub: "品牌資產" },
              { l: "品類", v: b.category ?? "—", sub: `信心 ${b.confidence ?? "—"}%` },
              {
                l: "主市場",
                v: b.primaryMarket,
                sub: `+ ${b.extendedMarkets.length} 延伸`,
              },
            ].map((c) => (
              <div
                key={c.l}
                style={{
                  padding: 14,
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
                    color: "var(--paper-ink-3)",
                    textTransform: "uppercase",
                  }}
                >
                  {c.l}
                </div>
                <div
                  style={{
                    fontFamily: "var(--font-numeric)",
                    fontSize: 26,
                    fontWeight: 700,
                    color: "var(--paper-ink)",
                    lineHeight: 1.1,
                    marginTop: 4,
                  }}
                >
                  {c.v}
                </div>
                <div style={{ fontSize: 10, color: "var(--paper-ink-3)", marginTop: 4 }}>
                  {c.sub}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <PageFooter page={2} pageCount={b.pageCount} />
    </A4Page>
  );
}
