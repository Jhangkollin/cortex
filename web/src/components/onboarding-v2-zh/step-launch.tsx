"use client";

/**
 * Step 5 — Launch settings + brand voice preview.
 *
 * Left column: deployment summary, voice tone picker (3 tones), T+0..T+7d
 * timeline. Right column: a live preview card whose answer copy hot-swaps
 * to match the selected tone, and an ink-900 → teal-900 launch hero with
 * an amber full-width CTA.
 */

import type { ExtractedBrand, LiveQuestion, Media, VoiceTone } from "./data";
import { Badge, Card, Icon, OnbButton, StepHead } from "./primitives";

export function StepLaunch({
  brand,
  pickedMedia,
  voiceTone,
  setVoiceTone,
  onLaunch,
  mediaNetwork,
  voiceTones,
  liveQuestions,
}: {
  brand: ExtractedBrand;
  pickedMedia: string[];
  voiceTone: VoiceTone["id"];
  setVoiceTone: (id: VoiceTone["id"]) => void;
  onLaunch: () => void;
  mediaNetwork: Media[];
  voiceTones: VoiceTone[];
  liveQuestions: LiveQuestion[];
}) {
  const mediaList = mediaNetwork.filter((m) => pickedMedia.includes(m.id));
  const productsOn = brand.products.filter((p) => p.picked);
  const tone = voiceTones.find((t) => t.id === voiceTone) ?? voiceTones[0];

  // 真實問題模擬：選用品牌意圖分數最高的讀者問題（每週問題管線，best-first）。
  // 不再使用寫死的範例；管線真的沒有資料時，退回中性的品牌導向提示，
  // 而不是不相關的示範問題。
  const featured = liveQuestions.length
    ? [...liveQuestions].sort((a, b) => b.score - a.score)[0]
    : null;
  const previewQuestion = featured?.text ?? `選擇 ${brand.name} 前，我應該了解什麼？`;
  const previewSource = featured
    ? `讀者 · ${featured.media} · ${featured.when}`
    : "讀者 · 你的媒體網路 · 本週";
  // 引用標籤改用品牌的真實啟用產品（原本寫死銀行產品）。最多 2 個以符合版面。
  const citationTags = productsOn.slice(0, 2).map((p) => p.name);

  const stats: Array<{ l: string; v: number; s: string; i: string }> = [
    { l: "上下文代理", v: mediaList.length, s: "對應媒體", i: "hub" },
    { l: "啟用產品", v: productsOn.length, s: "知識庫", i: "category" },
    { l: "競品監測", v: brand.competitors.filter((c) => c.picked).length, s: "家", i: "groups" },
  ];

  const timeline: Array<{ t: string; title: string; desc: string; color: string }> = [
    {
      t: "T+0",
      title: "Agent 部署",
      desc: `${mediaList.length} 個 Context Agent 連線到媒體`,
      color: "var(--brand-teal)",
    },
    {
      t: "T+30m",
      title: "首批草稿",
      desc: "Answer Pilot 對本週高強度問題開始草擬",
      color: "var(--brand-teal)",
    },
    {
      t: "T+24h",
      title: "首批 Answer 上線",
      desc: "通過 Brand Voice + 合規校驗後進入媒體",
      color: "var(--gold-deep)",
    },
    {
      t: "T+7d",
      title: "週報 + 建議",
      desc: "Cortex 整理表現、建議下一週方向",
      color: "var(--paper-ink-2)",
    },
  ];

  return (
    <div>
      <StepHead
        eyebrow="第 5 步 · 啟動 Agent"
        title="按下啟動，Cortex 就會把工作分派出去"
        subtitle="最後只剩一件事——挑你的 Brand Voice。Cortex 會以這個語調，在你選的媒體上回答讀者問題。"
      />

      <div className="onb-grid-launch" style={{ gap: 18, marginBottom: 18 }}>
        {/* LEFT */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <Card style={{ padding: 18 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
              <Icon name="rocket_launch" size={18} color="var(--brand-teal)" />
              <div style={{ fontSize: 13, fontWeight: 700, color: "var(--paper-ink)" }}>
                即將部署
              </div>
              <Badge color="teal" style={{ marginLeft: "auto" }}>
                5 個 Agent
              </Badge>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, 1fr)",
                gap: 10,
                marginBottom: 14,
              }}
            >
              {stats.map((s) => (
                <div
                  key={s.l}
                  style={{
                    padding: 12,
                    background: "var(--ink-warm-50)",
                    borderRadius: 6,
                  }}
                >
                  <Icon name={s.i} size={14} color="var(--brand-teal)" />
                  <div
                    style={{
                      fontFamily: "var(--font-numeric)",
                      fontWeight: 700,
                      fontSize: 22,
                      color: "var(--paper-ink)",
                      marginTop: 4,
                      lineHeight: 1.05,
                    }}
                  >
                    {s.v}
                  </div>
                  <div
                    style={{
                      fontSize: 10,
                      color: "var(--paper-ink-3)",
                      fontFamily: "var(--font-mono)",
                      marginTop: 2,
                    }}
                  >
                    {s.s}
                  </div>
                </div>
              ))}
            </div>

            <div
              style={{
                padding: 12,
                background: "var(--mly-teal-050)",
                border: "1px solid var(--mly-teal-100)",
                borderRadius: 6,
                fontSize: 12,
                color: "var(--mly-ink-800)",
                lineHeight: 1.6,
              }}
            >
              <Icon name="auto_awesome" size={13} color="var(--brand-teal)" /> 將部署到{" "}
              <strong>{mediaList.slice(0, 3).map((m) => m.name).join("、")}</strong>
              {mediaList.length > 3 ? ` 等 ${mediaList.length} 家媒體` : ""}，每家獨立 Context Agent。
            </div>
          </Card>

          {/* Voice tone picker */}
          <Card style={{ padding: 18 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
              <Icon name="campaign" size={18} color="var(--brand-teal)" />
              <div style={{ fontSize: 13, fontWeight: 700, color: "var(--paper-ink)" }}>
                Brand Voice 語調
              </div>
              <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--paper-ink-3)" }}>
                啟動後可在 Brand Studio 微調
              </span>
            </div>
            <div style={{ fontSize: 12, color: "var(--paper-ink-3)", marginBottom: 12 }}>
              選一種語調當基礎。右側即時預覽會根據選擇改變。
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
              {voiceTones.map((t) => {
                const isOn = voiceTone === t.id;
                return (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setVoiceTone(t.id)}
                    style={{
                      padding: 14,
                      borderRadius: 8,
                      background: isOn ? "var(--mly-teal-050)" : "#fff",
                      border: `1.5px solid ${isOn ? "var(--brand-teal)" : "var(--paper-border)"}`,
                      boxShadow: isOn ? "0 0 0 3px rgba(34,93,89,0.08)" : "none",
                      cursor: "pointer",
                      textAlign: "left",
                      transition: "all 120ms",
                      position: "relative",
                      fontFamily: "inherit",
                    }}
                    aria-pressed={isOn}
                  >
                    {isOn ? (
                      <div
                        style={{
                          position: "absolute",
                          top: 8,
                          right: 8,
                          width: 18,
                          height: 18,
                          borderRadius: "50%",
                          background: "var(--brand-teal)",
                          display: "grid",
                          placeItems: "center",
                        }}
                      >
                        <Icon name="check" size={11} color="#fff" />
                      </div>
                    ) : null}
                    <Icon name={t.icon} size={16} color="var(--brand-teal)" />
                    <div
                      style={{
                        fontSize: 13,
                        fontWeight: 700,
                        color: "var(--paper-ink)",
                        marginTop: 8,
                        marginBottom: 2,
                      }}
                    >
                      {t.label}
                    </div>
                    <div style={{ fontSize: 11, color: "var(--paper-ink-3)" }}>{t.desc}</div>
                  </button>
                );
              })}
            </div>
          </Card>

          {/* Schedule preview */}
          <Card style={{ padding: 18 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
              <Icon name="schedule" size={18} color="var(--brand-teal)" />
              <div style={{ fontSize: 13, fontWeight: 700, color: "var(--paper-ink)" }}>
                啟動後的時間表
              </div>
              <Badge color="amber" style={{ marginLeft: "auto" }}>
                自動執行
              </Badge>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {timeline.map((r) => (
                <div
                  key={r.t}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "auto 1fr auto",
                    gap: 12,
                    alignItems: "center",
                    padding: "8px 10px",
                    borderRadius: 6,
                    background: "var(--ink-warm-50)",
                  }}
                >
                  <div
                    style={{
                      width: 44,
                      padding: "3px 0",
                      borderRadius: 4,
                      textAlign: "center",
                      background: "#fff",
                      border: `1px solid ${r.color}`,
                      color: r.color,
                      fontFamily: "var(--font-mono)",
                      fontSize: 11,
                      fontWeight: 700,
                    }}
                  >
                    {r.t}
                  </div>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "var(--paper-ink)" }}>
                      {r.title}
                    </div>
                    <div style={{ fontSize: 11, color: "var(--paper-ink-3)", marginTop: 1 }}>
                      {r.desc}
                    </div>
                  </div>
                  <Icon name="chevron_right" size={16} color="var(--mly-ink-300)" />
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* RIGHT — preview + launch hero */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <Card style={{ padding: 0, overflow: "hidden" }}>
            <div
              style={{
                padding: "12px 18px",
                background: "var(--ink-warm-50)",
                borderBottom: "1px solid var(--mly-ink-100)",
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <Icon name="auto_awesome" size={16} color="var(--gold-deep)" />
              <span style={{ fontSize: 13, fontWeight: 700, color: "var(--paper-ink)" }}>
                Brand Voice 預覽
              </span>
              <Badge color="real" style={{ marginLeft: "auto" }}>
                實際問題模擬
              </Badge>
            </div>

            <div style={{ padding: 18 }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 10,
                  marginBottom: 14,
                }}
              >
                <div
                  style={{
                    width: 30,
                    height: 30,
                    borderRadius: "50%",
                    background: "var(--mly-ink-100)",
                    display: "grid",
                    placeItems: "center",
                    flexShrink: 0,
                  }}
                >
                  <Icon name="person" size={16} color="var(--paper-ink-3)" />
                </div>
                <div style={{ flex: 1 }}>
                  <div
                    style={{
                      fontSize: 11,
                      color: "var(--paper-ink-3)",
                      fontWeight: 600,
                      marginBottom: 4,
                    }}
                  >
                    {previewSource}
                  </div>
                  <div style={{ fontSize: 14, color: "var(--mly-ink-800)", lineHeight: 1.5 }}>
                    “{previewQuestion}”
                  </div>
                </div>
              </div>

              <div style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
                <div
                  style={{
                    width: 30,
                    height: 30,
                    borderRadius: "50%",
                    background: `linear-gradient(135deg, ${brand.brandColor}, var(--mly-teal-800))`,
                    display: "grid",
                    placeItems: "center",
                    flexShrink: 0,
                    color: "#fff",
                    fontWeight: 700,
                    fontSize: 14,
                  }}
                >
                  {brand.monogram}
                </div>
                <div style={{ flex: 1 }}>
                  <div
                    style={{
                      fontSize: 11,
                      color: "var(--brand-teal)",
                      fontWeight: 600,
                      marginBottom: 4,
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                    }}
                  >
                    {brand.name} · Brand Agent
                    <span style={{ width: 4, height: 4, borderRadius: "50%", background: "var(--mly-ink-300)" }} />
                    <span style={{ color: "var(--paper-ink-3)" }}>{tone.label}</span>
                  </div>
                  <div
                    key={voiceTone}
                    style={{
                      fontSize: 14,
                      color: "var(--mly-ink-800)",
                      lineHeight: 1.7,
                      padding: 16,
                      background: "var(--mly-teal-050)",
                      border: "1px solid var(--mly-teal-100)",
                      borderRadius: 8,
                      animation: "mly-fade-in 240ms",
                    }}
                  >
                    {tone.sample}
                  </div>
                  <div
                    style={{
                      display: "flex",
                      flexWrap: "wrap",
                      gap: 6,
                      marginTop: 10,
                      fontSize: 11,
                      color: "var(--paper-ink-3)",
                    }}
                  >
                    {citationTags.map((name) => (
                      <span
                        key={name}
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: 4,
                          padding: "2px 8px",
                          background: "var(--mly-ink-050)",
                          borderRadius: 999,
                        }}
                      >
                        <Icon name="link" size={11} /> {name}
                      </span>
                    ))}
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 4,
                        padding: "2px 8px",
                        background: "#E0F2F1",
                        color: "var(--mly-success)",
                        borderRadius: 999,
                        fontWeight: 600,
                      }}
                    >
                      <Icon name="verified" size={11} /> 引用核驗
                    </span>
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 4,
                        padding: "2px 8px",
                        background: "#E0F2F1",
                        color: "var(--mly-success)",
                        borderRadius: 999,
                        fontWeight: 600,
                      }}
                    >
                      <Icon name="shield" size={11} /> 合規通過
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div
              style={{
                padding: "10px 18px",
                borderTop: "1px solid var(--mly-ink-100)",
                background: "var(--ink-warm-50)",
                display: "flex",
                gap: 18,
                fontSize: 11,
                color: "var(--paper-ink-3)",
                fontFamily: "var(--font-mono)",
              }}
            >
              <span>
                <Icon name="schedule" size={12} /> 1.2s
              </span>
              <span>
                <Icon name="token" size={12} /> 412 詞元
              </span>
              <span>
                <Icon name="auto_awesome" size={12} /> 評分 9.2/10
              </span>
              <span style={{ marginLeft: "auto" }}>v3.2 · Mlytics Cortex</span>
            </div>
          </Card>

          {/* Launch hero — Light Edition (handoff §3.3). Cream paper
              gradient + paper-border + gold-soft icon backplate + gold
              solid CTA. */}
          <Card
            style={{
              padding: 22,
              background:
                "linear-gradient(135deg, var(--paper-highlight) 0%, var(--paper) 60%, var(--paper-warm) 100%)",
              color: "var(--paper-ink)",
              border: "1px solid var(--paper-border)",
              position: "relative",
              overflow: "hidden",
              boxShadow:
                "0 12px 28px -10px rgba(var(--paper-ink-rgb), 0.18), 0 2px 6px -2px rgba(var(--paper-ink-rgb), 0.06)",
            }}
          >
            <div
              aria-hidden
              style={{
                position: "absolute",
                right: -80,
                top: -80,
                width: 260,
                height: 260,
                borderRadius: "50%",
                border: "1px solid rgba(var(--gold-rgb), 0.18)",
                pointerEvents: "none",
              }}
            >
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  background:
                    "conic-gradient(from 0deg, rgba(var(--gold-rgb), 0.20), transparent 28%)",
                  borderRadius: "50%",
                  animation: "mly-radar-sweep 4s linear infinite",
                }}
              />
            </div>

            <div
              style={{
                position: "relative",
                display: "flex",
                alignItems: "center",
                gap: 16,
                marginBottom: 14,
              }}
            >
              <div
                style={{
                  width: 56,
                  height: 56,
                  borderRadius: 14,
                  background: "var(--gold-soft)",
                  display: "grid",
                  placeItems: "center",
                  position: "relative",
                  border: "1px solid var(--gold-border)",
                }}
              >
                <Icon name="bolt" size={28} color="var(--gold)" />
                <div
                  style={{
                    position: "absolute",
                    inset: -3,
                    borderRadius: 17,
                    border: "1px solid rgba(var(--gold-rgb), 0.35)",
                    animation: "mly-pulse 1.6s ease-in-out infinite",
                  }}
                />
              </div>
              <div style={{ flex: 1 }}>
                <div
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    letterSpacing: "0.1em",
                    textTransform: "uppercase",
                    color: "var(--gold-deep)",
                    marginBottom: 4,
                  }}
                >
                  最後一步
                </div>
                <div
                  style={{
                    fontSize: 18,
                    fontWeight: 700,
                    color: "var(--paper-ink)",
                  }}
                >
                  啟動你的 Brand Agent
                </div>
                <div
                  style={{
                    fontSize: 12,
                    color: "var(--paper-ink-2)",
                    marginTop: 4,
                    lineHeight: 1.5,
                  }}
                >
                  {mediaList.length} media · {productsOn.length} products · {tone.label}
                </div>
              </div>
            </div>
            <OnbButton
              variant="gold"
              size="lg"
              icon="rocket_launch"
              onClick={onLaunch}
              glow="0 8px 18px -4px rgba(var(--gold-rgb), 0.45)"
              style={{ width: "100%", borderRadius: 8, fontWeight: 700 }}
            >
              啟動 Brand Agent
            </OnbButton>
            <div
              style={{
                marginTop: 10,
                fontSize: 11,
                color: "var(--paper-ink-3)",
                textAlign: "center",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 6,
              }}
            >
              <Icon name="lock" size={11} color="var(--paper-ink-3)" /> 你的資料只用在 Cortex 內部 · 啟動後可隨時暫停
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
