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
  // 偵測本批問題是來自 AIGC 媒體網路即時快照,還是來自 D8 LLM-synth fallback
  // (matcher 對 synth 問題的 id 加 "synth-" 前綴)。決定 badge 文案——精靈不可
  // 把品牌側模擬的問題標示為「本週真實樣本」。
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
      l: "本週相關問題",
      v: <CountUp to={questions.length} duration={700} />,
      s: "為你品牌篩選",
      color: "var(--mly-ink-900)",
    },
    {
      l: "高購買意圖",
      v: <CountUp to={highIntent} duration={700} />,
      s: "意圖強度 ≥ 80",
      color: "var(--cortex-amber-600)",
    },
    {
      l: "競品被提及",
      v: <CountUp to={competitorMentions} duration={700} />,
      s: "次 · 本週樣本",
      color: "var(--mly-warn-strong)",
    },
    {
      l: "你的覆蓋率",
      v: (
        <span>
          0<span style={{ fontSize: 18, fontWeight: 500 }}>%</span>
        </span>
      ),
      s: "品牌回應 = 0",
      color: "var(--mly-danger)",
      danger: true,
    },
  ];

  const filters: Array<{ id: FilterId; l: string; c: number }> = [
    { id: "all", l: "全部", c: questions.length },
    { id: "Explore", l: "探索", c: intentCounts.Explore },
    { id: "Understand", l: "了解", c: intentCounts.Understand },
    { id: "Evaluate", l: "評估", c: intentCounts.Evaluate },
    { id: "Act", l: "行動", c: intentCounts.Act },
  ];

  return (
    <div>
      <StepHead
        eyebrow="第 4 步 · 本週問題"
        title="你的受眾這週在問什麼"
        subtitle={
          allSynth
            ? "品牌資料預覽——本週媒體網路沒有足夠的即時品類訊號,因此這些問題是由你的品牌資料(品類、產品、競品)合成生成,呈現此類讀者正在做的決策樣態。"
            : "這是本週媒體網路中與你品類相關的真實問題。讀者正在做購買決策——目前你的品牌幾乎完全缺席。"
        }
        accent={`從 ${brand.url} 對應品類 · 本週 ${questions.length} 則`}
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
          意圖框架
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
                  <Icon name="forum" size={12} /> {q.asks.toLocaleString()} 次提問
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
                    <Icon name="record_voice_over" size={11} /> 競品：
                    {q.competitorMentions.join("、")}
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
                  強度
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
                ● 品牌缺席
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
              ? `本週這些問題累計約 ${totalAsks.toLocaleString()} 次讀者互動`
              : "品牌資料預覽——確認設定即可啟動即時訊號覆蓋"}
          </div>
          <div style={{ fontSize: 12, color: "rgba(255,255,255,0.7)", lineHeight: 1.5 }}>
            這些讀者正在做你品類的購買決策，總提問 {totalAsks.toLocaleString()} 次。
            確認設定後，Cortex 會在下一步啟動 Agent 開始覆蓋這些問題。
          </div>
        </div>
        <Badge color="real">
          {allSynth ? "合成預覽" : someSynth ? "真實 + 合成" : "本週真實樣本"}
        </Badge>
      </div>
    </div>
  );
}
