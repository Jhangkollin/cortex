"use client";

/**
 * Step 4 — This week's questions.
 *
 * Four KPI cards (one pulsing-red "Coverage = 0%" to trigger urgency), then
 * intent-frame filter chips, then a list of real reader questions with
 * intent pill and intensity score. Footer is an ink-900 → teal-900 callout
 * that quantifies the missed reach.
 */

import { useState } from "react";

import type { ExtractedBrand, LiveQuestion } from "./data";
import { INTENT_COLOR } from "./data";
import { Badge, Card, CountUp, Icon, IntentPill, StepHead } from "./primitives";

type Intent = keyof typeof INTENT_COLOR;
type FilterId = "all" | Intent;

export function StepQuestions({
  brand,
  liveQuestions,
}: {
  brand: ExtractedBrand;
  liveQuestions: LiveQuestion[];
}) {
  const [filter, setFilter] = useState<FilterId>("all");
  const questions = liveQuestions;
  const filtered = filter === "all" ? questions : questions.filter((q) => q.intent === filter);

  const totalAsks = questions.reduce((s, q) => s + q.asks, 0);
  const highIntent = questions.filter((q) => q.score >= 80).length;
  const competitorMentions = questions.reduce((s, q) => s + q.competitorMentions.length, 0);
  // Detect whether this batch came from the live AIGC snapshot or from D8's
  // LLM-synth fallback (the matcher prefixes synth ids with `synth-`). Drives
  // the badge label so the wizard never claims "real weekly sample" when the
  // questions are profile-derived simulation.
  const allSynth = questions.length > 0 && questions.every((q) => q.id.startsWith("synth-"));
  const someSynth = questions.length > 0 && questions.some((q) => q.id.startsWith("synth-"));

  const intentCounts: Record<Intent, number> = {
    Explore: questions.filter((q) => q.intent === "Explore").length,
    Understand: questions.filter((q) => q.intent === "Understand").length,
    Evaluate: questions.filter((q) => q.intent === "Evaluate").length,
    Act: questions.filter((q) => q.intent === "Act").length,
  };

  const kpis = [
    {
      l: "Relevant questions",
      v: <CountUp to={questions.length} duration={700} />,
      s: "matched for your brand",
      color: "var(--mly-ink-900)",
    },
    {
      l: "High purchase intent",
      v: <CountUp to={highIntent} duration={700} />,
      s: "intensity ≥ 80",
      color: "var(--cortex-amber-600)",
    },
    {
      l: "Competitor mentions",
      v: <CountUp to={competitorMentions} duration={700} />,
      s: "this week",
      color: "var(--mly-warn-strong)",
    },
    {
      l: "Your coverage",
      v: (
        <span>
          0<span style={{ fontSize: 18, fontWeight: 500 }}>%</span>
        </span>
      ),
      s: "Brand answers = 0",
      color: "var(--mly-danger)",
      danger: true,
    },
  ];

  const filters: Array<{ id: FilterId; l: string; c: number }> = [
    { id: "all", l: "All", c: questions.length },
    { id: "Explore", l: "Explore", c: intentCounts.Explore },
    { id: "Understand", l: "Understand", c: intentCounts.Understand },
    { id: "Evaluate", l: "Evaluate", c: intentCounts.Evaluate },
    { id: "Act", l: "Act", c: intentCounts.Act },
  ];

  return (
    <div>
      <StepHead
        eyebrow="Step 4 · Weekly questions"
        title="What your audience is asking this week"
        subtitle={
          allSynth
            ? "Profile-derived preview — your media network didn't surface enough live category signal this week, so these questions are synthesized from your brand profile (category, products, competitors). They show the kinds of decisions your readers are making right now."
            : "Real reader questions from your media network, filtered to your category. They're making purchase decisions right now — and your brand is almost entirely absent."
        }
        accent={`From ${brand.url}'s category · ${questions.length} question${questions.length === 1 ? "" : "s"} this week`}
      />

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 18 }}>
        {kpis.map((k) => (
          <Card
            key={k.l}
            style={{
              padding: 14,
              position: "relative",
              overflow: "hidden",
              background: k.danger ? "linear-gradient(180deg, #FFF5F5, #fff)" : "#fff",
              border: k.danger ? "1px solid #FBC9C9" : "1px solid var(--mly-ink-150)",
            }}
          >
            <div
              style={{
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: "0.1em",
                textTransform: "uppercase",
                color: "var(--mly-ink-500)",
              }}
            >
              {k.l}
            </div>
            <div
              style={{
                fontFamily: "var(--font-numeric)",
                fontWeight: 700,
                fontSize: 28,
                color: k.color,
                marginTop: 6,
                lineHeight: 1.05,
                letterSpacing: "-0.02em",
              }}
            >
              {k.v}
            </div>
            <div
              style={{
                fontSize: 11,
                color: "var(--mly-ink-500)",
                marginTop: 3,
                fontFamily: "var(--font-mono)",
              }}
            >
              {k.s}
            </div>
            {k.danger ? (
              <div
                style={{
                  position: "absolute",
                  top: 10,
                  right: 10,
                  width: 22,
                  height: 22,
                  borderRadius: "50%",
                  background: "#FFEBEE",
                  display: "grid",
                  placeItems: "center",
                  animation: "mly-pulse 1.5s ease-in-out infinite",
                }}
              >
                <Icon name="priority_high" size={13} color="var(--mly-danger)" />
              </div>
            ) : null}
          </Card>
        ))}
      </div>

      {/* Filter chips */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          marginBottom: 10,
          flexWrap: "wrap",
        }}
      >
        <span
          style={{
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "var(--mly-ink-500)",
            marginRight: 4,
          }}
        >
          Intent frame
        </span>
        {filters.map((f) => {
          const isOn = filter === f.id;
          return (
            <button
              key={f.id}
              type="button"
              onClick={() => setFilter(f.id)}
              style={{
                padding: "5px 12px",
                borderRadius: 999,
                background: isOn ? "var(--mly-ink-900)" : "#fff",
                color: isOn ? "#fff" : "var(--mly-ink-700)",
                border: `1px solid ${isOn ? "var(--mly-ink-900)" : "var(--mly-ink-200)"}`,
                fontSize: 12,
                fontWeight: 500,
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
                fontFamily: "inherit",
              }}
            >
              {f.l}
              <span
                style={{
                  padding: "0 6px",
                  fontSize: 10,
                  fontWeight: 700,
                  borderRadius: 999,
                  fontFamily: "var(--font-numeric)",
                  background: isOn ? "rgba(255,255,255,0.18)" : "var(--mly-ink-050)",
                  color: isOn ? "#fff" : "var(--mly-ink-500)",
                }}
              >
                {f.c}
              </span>
            </button>
          );
        })}
      </div>

      <div className="onb-grid-1-2" style={{ gap: 8 }}>
        {filtered.map((q, idx) => (
          <div
            key={q.id}
            style={{
              display: "grid",
              gridTemplateColumns: "auto 1fr auto auto",
              gap: 16,
              alignItems: "center",
              padding: "14px 16px",
              background: "#fff",
              border: "1px solid var(--mly-ink-150)",
              borderRadius: 8,
              animation: `mly-fade-up 280ms ${idx * 25}ms backwards`,
            }}
          >
            <div
              style={{
                width: 28,
                height: 28,
                display: "grid",
                placeItems: "center",
                borderRadius: 6,
                background: "var(--mly-ink-050)",
                color: "var(--mly-ink-400)",
                fontFamily: "var(--font-mono)",
                fontSize: 11,
                fontWeight: 700,
              }}
            >
              {String(idx + 1).padStart(2, "0")}
            </div>
            <div style={{ minWidth: 0 }}>
              <div
                style={{
                  fontSize: 14,
                  color: "var(--mly-ink-900)",
                  fontWeight: 500,
                  marginBottom: 5,
                  lineHeight: 1.4,
                }}
              >
                “{q.text}”
              </div>
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 12,
                  fontSize: 11,
                  color: "var(--mly-ink-500)",
                  fontFamily: "var(--font-mono)",
                  alignItems: "center",
                }}
              >
                <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                  <Icon name="newspaper" size={12} /> {q.media}
                </span>
                <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                  <Icon name="forum" size={12} /> {q.asks.toLocaleString()} asks
                </span>
                <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                  <Icon name="schedule" size={12} /> {q.when}
                </span>
                {q.competitorMentions.length > 0 ? (
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 4,
                      padding: "1px 8px",
                      borderRadius: 999,
                      background: "#FFF5E6",
                      color: "var(--mly-warn-strong)",
                      fontWeight: 600,
                    }}
                  >
                    <Icon name="record_voice_over" size={11} /> Competitors:{" "}
                    {q.competitorMentions.join(", ")}
                  </span>
                ) : null}
              </div>
            </div>
            <IntentPill intent={q.intent} />
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{ textAlign: "right" }}>
                <div
                  style={{
                    fontFamily: "var(--font-numeric)",
                    fontWeight: 700,
                    fontSize: 20,
                    color: q.score >= 85 ? "var(--cortex-amber-600)" : "var(--mly-ink-800)",
                    lineHeight: 1,
                  }}
                >
                  {q.score}
                </div>
                <div
                  style={{
                    fontSize: 9,
                    color: "var(--mly-ink-400)",
                    fontFamily: "var(--font-mono)",
                    letterSpacing: "0.04em",
                  }}
                >
                  Intensity
                </div>
              </div>
              <div
                style={{
                  padding: "4px 10px",
                  border: "1px solid var(--mly-danger)",
                  color: "var(--mly-danger)",
                  fontSize: 11,
                  fontWeight: 700,
                  borderRadius: 999,
                  background: "#FFF5F5",
                  whiteSpace: "nowrap",
                }}
              >
                ● Brand absent
              </div>
            </div>
          </div>
        ))}
      </div>

      <div
        style={{
          marginTop: 16,
          padding: 18,
          borderRadius: 10,
          background: "linear-gradient(135deg, var(--mly-ink-900), var(--mly-teal-900))",
          color: "#fff",
          display: "grid",
          gridTemplateColumns: "auto 1fr auto",
          gap: 16,
          alignItems: "center",
        }}
      >
        <div
          style={{
            width: 44,
            height: 44,
            borderRadius: 10,
            background: "rgba(245,158,11,0.15)",
            display: "grid",
            placeItems: "center",
          }}
        >
          <Icon name="warning_amber" size={22} color="var(--cortex-amber-200)" />
        </div>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, color: "#fff", marginBottom: 4 }}>
            {totalAsks > 0
              ? `~${totalAsks.toLocaleString()} reader engagements across these questions`
              : "Brand-profile preview — confirm to start covering live signal"}
          </div>
          <div style={{ fontSize: 12, color: "rgba(255,255,255,0.7)", lineHeight: 1.5 }}>
            These readers are actively making category decisions. Confirm your
            settings on the next step and Cortex will spin up agents to start
            covering them.
          </div>
        </div>
        <Badge color="real">
          {allSynth
            ? "Synthesized preview"
            : someSynth
              ? "Live + synthesized"
              : "Real weekly sample"}
        </Badge>
      </div>
    </div>
  );
}
