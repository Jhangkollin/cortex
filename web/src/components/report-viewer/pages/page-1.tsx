import type { BrandIqReport } from "@/lib/cortex-api";
import { A4Page } from "../shared/a4-page";
import { ConstellationSVG } from "../shared/constellation-svg";
import { SECTIONS } from "../sections";

interface Page1Props {
  report: BrandIqReport;
}

/**
 * P1 — Cover · Brand Constellation (Light Edition).
 *
 * The cover overrides the default A4 paper bg with a vertical cream gradient
 * (paper-highlight → paper → paper-warm) plus a faint dot-grid paper texture.
 * All accents are gold (eyebrow + pull-quote tag + Strategic Pin) and the
 * tagline picks up brand-teal italic for the brand voice line.
 */
export function Page1({ report }: Page1Props) {
  const b = report.meta;
  return (
    <A4Page>


      {/* top bar */}
      <div
        style={{
          position: "absolute",
          top: 26,
          left: 36,
          right: 36,
          display: "flex",
          justifyContent: "space-between",
          fontFamily: "var(--font-mono)",
          fontSize: 9,
          letterSpacing: "0.22em",
          textTransform: "uppercase",
          color: "var(--paper-ink-3)",
        }}
      >
        <span>Cortex · Brand Intelligence Bureau</span>
        <span>{b.reportId}</span>
      </div>
      <div
        style={{
          position: "absolute",
          left: 36,
          right: 36,
          top: 50,
          height: 1,
          background: "#d5dee0",
        }}
      />

      {/* eyebrow */}
      <div
        style={{
          position: "absolute",
          left: 36,
          top: 80,
          fontFamily: "var(--font-mono)",
          fontSize: 11,
          letterSpacing: "0.2em",
          textTransform: "uppercase",
          color: "var(--mly-teal-400)",
          fontWeight: 700,
        }}
      >
        ◇ Brand Constellation · Vol. 01
      </div>

      {/* brand name + tagline */}
      <div style={{ position: "absolute", left: 36, right: 36, top: 116 }}>
        <div
          style={{
            fontSize: 60,
            fontWeight: 800,
            color: "var(--paper-ink)",
            letterSpacing: "-0.025em",
            lineHeight: 1.0,
          }}
        >
          {b.subject}
        </div>
        <div
          style={{
            fontFamily: "var(--font-serif)",
            fontStyle: "italic",
            fontSize: 36,
            fontWeight: 500,
            color: "var(--mly-teal-700)",
            letterSpacing: "-0.02em",
            lineHeight: 1.1,
            marginTop: 4,
          }}
        >
          The shape of a brand.
        </div>
      </div>

      {/* constellation centerpiece */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 268,
          display: "grid",
          placeItems: "center",
        }}
      >
        <ConstellationSVG
          size={420}
          brandMono={b.monogram}
          accent="var(--mly-teal-700)"
          mediaLabels={report.mediaNetwork.map((m) => m.name)}
          productCount={report.productLines.length || undefined}
        />
      </div>

      {/* legend */}
      <div
        style={{
          position: "absolute",
          left: 36,
          top: 300,
          fontFamily: "var(--font-mono)",
          fontSize: 10,
          color: "var(--paper-ink-3)",
          letterSpacing: "0.06em",
        }}
      >
        <div
          style={{
            marginBottom: 12,
            fontSize: 9,
            letterSpacing: "0.18em",
            textTransform: "uppercase",
            color: "var(--paper-ink-4)",
          }}
        >
          LEGEND
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
          <span
            style={{
              width: 11,
              height: 11,
              borderRadius: "50%",
              background: "var(--mly-teal-700)",
            }}
          />
          品牌核心
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
          <span
            style={{
              width: 7,
              height: 7,
              borderRadius: "50%",
              background: "var(--mly-teal-700)",
              opacity: 0.7,
            }}
          />
          產品線 · {report.productLines.length}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 9,
              height: 9,
              borderRadius: "50%",
              background: "#fff",
              border: "1.5px solid var(--mly-teal-700)",
            }}
          />
          媒體節點 · {report.mediaNetwork.length}
        </div>
      </div>

      {/* observation / market */}
      <div
        style={{
          position: "absolute",
          right: 36,
          top: 300,
          textAlign: "right",
          fontFamily: "var(--font-mono)",
          fontSize: 10,
          color: "var(--paper-ink-3)",
        }}
      >
        <div
          style={{
            marginBottom: 12,
            fontSize: 9,
            letterSpacing: "0.18em",
            textTransform: "uppercase",
            color: "var(--paper-ink-4)",
          }}
        >
          OBSERVATION
        </div>
        {b.windowFrom ? <div style={{ marginBottom: 6 }}>{b.windowFrom} →</div> : null}
        {b.windowTo ? <div style={{ marginBottom: 12 }}>{b.windowTo}</div> : null}
        <div
          style={{
            fontSize: 9,
            letterSpacing: "0.18em",
            textTransform: "uppercase",
            color: "var(--paper-ink-4)",
          }}
        >
          MARKET
        </div>
        <div style={{ marginTop: 6 }}>{b.primaryMarket}</div>
        {b.extendedMarkets.length > 0 ? (
          <div style={{ color: "var(--paper-ink-4)", marginTop: 2 }}>
            + {b.extendedMarkets.join(" · ")}
          </div>
        ) : null}
      </div>

      {/* strategic pin pull quote — uses the brand-specific LLM synthesis
          (coreJudgement). Omitted entirely when the contract has no judgement
          so the cover never asserts copy that isn't in `report`. */}
      {report.coreJudgement ? (
        <div
          style={{
            position: "absolute",
            left: 36,
            right: 36,
            top: 740,
            paddingTop: 18,
            borderTop: "1px solid #d5dee0",
            fontFamily: "var(--font-serif-tc)",
            fontSize: 17,
            color: "var(--paper-ink-2)",
            fontStyle: "italic",
            lineHeight: 1.55,
          }}
        >
          「{report.coreJudgement}」
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontStyle: "normal",
              fontSize: 10,
              color: "var(--mly-teal-400)",
              marginTop: 8,
              letterSpacing: "0.14em",
              textTransform: "uppercase",
            }}
          >
            — Cortex Brand IQ · Strategic Pin
          </div>
        </div>
      ) : null}

      {/* contents strip */}
      <div
        style={{
          position: "absolute",
          left: 36,
          right: 36,
          bottom: 88,
          display: "grid",
          gridTemplateColumns: "repeat(5, 1fr)",
          gap: 14,
          paddingTop: 14,
          borderTop: "1px solid #d5dee0",
        }}
      >
        {SECTIONS.filter((s) => s.coverHighlight).map((s) => (
          <div key={s.n} style={{ fontFamily: "var(--font-mono)" }}>
            <div
              style={{
                fontSize: 9,
                letterSpacing: "0.18em",
                color: "var(--paper-ink-4)",
              }}
            >
              SEC · {s.coverSec}
            </div>
            <div
              style={{
                fontFamily: "var(--font-serif-tc)",
                fontSize: 14,
                fontWeight: 600,
                color: "var(--paper-ink)",
                marginTop: 6,
              }}
            >
              {s.toc}
            </div>
            <div
              style={{ fontSize: 10, color: "var(--paper-ink-4)", marginTop: 4 }}
            >
              p.{String(s.n).padStart(2, "0")}
            </div>
          </div>
        ))}
      </div>

      {/* footer */}
      <div
        style={{
          position: "absolute",
          left: 36,
          right: 36,
          bottom: 30,
          display: "flex",
          justifyContent: "space-between",
          fontFamily: "var(--font-mono)",
          fontSize: 9,
          letterSpacing: "0.22em",
          textTransform: "uppercase",
          color: "var(--paper-ink-3)",
        }}
      >
        <span>Confidential · {b.preparedFor}</span>
        <span>{b.preparedBy}</span>
      </div>
    </A4Page>
  );
}
