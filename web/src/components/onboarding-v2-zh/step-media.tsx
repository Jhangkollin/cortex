"use client";

/**
 * Step 3 — Media network selection.
 *
 * 2-up grid of media cards (selectable) + a sticky side card that totalises
 * weekly reach and shows a competitor-mention warning when there's at least
 * one tracked competitor.
 */

import type { ExtractedBrand, Media } from "./data";
import { Card, CountUp, Icon, StepHead } from "./primitives";

export function StepMedia({
  brand,
  picked,
  setPicked,
  mediaNetwork,
}: {
  brand: ExtractedBrand;
  picked: string[];
  setPicked: (next: string[]) => void;
  mediaNetwork: Media[];
}) {
  const toggle = (id: string) =>
    setPicked(picked.includes(id) ? picked.filter((x) => x !== id) : [...picked, id]);

  const selected = mediaNetwork.filter((m) => picked.includes(m.id));
  const totalReach = selected.reduce((s, m) => s + (m.weeklyReaders ?? 0), 0);
  const competitorList = brand.competitors.filter((c) => c.picked).map((c) => c.name);

  return (
    <div>
      <StepHead
        eyebrow="第 3 步 · 媒體網絡"
        title="你的受眾在這些媒體上"
        subtitle={`根據「${brand.category.value}」與 ${brand.region.join("・")}，Cortex 從媒體網絡找出 ${mediaNetwork.length} 家高度相關的媒體，並為每家配對對應的 Context Agent。`}
        accent="分析完成 · 動態更新中"
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1.6fr 1fr",
          gap: 18,
          alignItems: "flex-start",
        }}
      >
        <div className="onb-grid-2-3" style={{ gap: 10 }}>
          {mediaNetwork.map((m, idx) => {
            const isOn = picked.includes(m.id);
            return (
              <button
                key={m.id}
                type="button"
                onClick={() => toggle(m.id)}
                style={{
                  textAlign: "left",
                  display: "block",
                  padding: 14,
                  borderRadius: 10,
                  background: "#fff",
                  border: `1.5px solid ${isOn ? "var(--mly-teal-600)" : "var(--mly-ink-150)"}`,
                  boxShadow: isOn
                    ? "0 0 0 3px rgba(34,93,89,0.10)"
                    : "0 1px 2px rgba(0,0,0,0.04)",
                  cursor: "pointer",
                  transition: "all 120ms",
                  animation: `mly-fade-up 320ms ${idx * 35}ms backwards`,
                  fontFamily: "inherit",
                }}
                aria-pressed={isOn}
              >
                <div style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
                  <div
                    style={{
                      width: 38,
                      height: 38,
                      borderRadius: 8,
                      flexShrink: 0,
                      background: `linear-gradient(135deg, var(--mly-teal-${isOn ? "400" : "100"}), var(--mly-teal-${isOn ? "700" : "050"}))`,
                      color: "#fff",
                      display: "grid",
                      placeItems: "center",
                      fontFamily: "var(--font-numeric)",
                      fontWeight: 700,
                      fontSize: 16,
                    }}
                  >
                    {m.name.charAt(0)}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                      <span
                        style={{
                          fontSize: 14,
                          fontWeight: 700,
                          color: "var(--mly-ink-900)",
                        }}
                      >
                        {m.name}
                      </span>
                      <Icon
                        name={
                          m.trend === "up"
                            ? "trending_up"
                            : m.trend === "down"
                              ? "trending_down"
                              : "trending_flat"
                        }
                        size={13}
                        color={
                          m.trend === "up"
                            ? "var(--mly-success)"
                            : m.trend === "down"
                              ? "var(--mly-danger)"
                              : "var(--mly-ink-400)"
                        }
                      />
                    </div>
                    <div style={{ fontSize: 11, color: "var(--mly-ink-500)", marginTop: 1 }}>
                      {m.audience}
                    </div>
                  </div>
                  <div
                    style={{
                      width: 20,
                      height: 20,
                      borderRadius: 5,
                      background: isOn ? "var(--mly-teal-600)" : "transparent",
                      border: `1.5px solid ${isOn ? "var(--mly-teal-600)" : "var(--mly-ink-300)"}`,
                      display: "grid",
                      placeItems: "center",
                      flexShrink: 0,
                    }}
                  >
                    {isOn ? <Icon name="check" size={13} color="#fff" /> : null}
                  </div>
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr auto",
                    gap: 8,
                    marginTop: 10,
                    alignItems: "center",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                      fontSize: 11,
                      color: "var(--mly-teal-700)",
                    }}
                  >
                    <Icon name="smart_toy" size={12} />
                    <span style={{ fontWeight: 600 }}>{m.contextAgent}</span>
                  </div>
                  <div style={{ display: "flex", alignItems: "baseline", gap: 3 }}>
                    <span
                      style={{
                        fontFamily: "var(--font-numeric)",
                        fontSize: 18,
                        fontWeight: 700,
                        lineHeight: 1,
                        color: isOn ? "var(--mly-teal-700)" : "var(--mly-ink-300)",
                      }}
                    >
                      {m.relevance}
                    </span>
                    <span
                      style={{
                        fontSize: 9,
                        color: "var(--mly-ink-400)",
                        letterSpacing: "0.04em",
                        fontWeight: 600,
                      }}
                    >
                      相關
                    </span>
                  </div>
                </div>

                <div
                  style={{
                    marginTop: 8,
                    paddingTop: 8,
                    borderTop: "1px dashed var(--mly-ink-150)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                    {m.topics.map((t) => (
                      <span
                        key={t}
                        style={{
                          padding: "1px 6px",
                          fontSize: 10,
                          fontWeight: 500,
                          background: isOn ? "var(--mly-teal-050)" : "var(--mly-ink-050)",
                          color: isOn ? "var(--mly-teal-700)" : "var(--mly-ink-600)",
                          borderRadius: 3,
                        }}
                      >
                        #{t}
                      </span>
                    ))}
                  </div>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: 10,
                      color: "var(--mly-ink-500)",
                    }}
                  >
                    {m.weeklyReaders != null ? `${(m.weeklyReaders / 1_000).toFixed(0)}K/週` : "—"}
                  </span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Side summary */}
        <Card style={{ padding: 18, position: "sticky", top: 100 }}>
          <div
            style={{
              fontSize: 10,
              fontWeight: 700,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "var(--mly-ink-500)",
            }}
          >
            媒體網絡覆蓋
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "baseline",
              gap: 6,
              marginTop: 8,
              marginBottom: 8,
            }}
          >
            <span
              style={{
                fontFamily: "var(--font-numeric)",
                fontSize: 38,
                fontWeight: 700,
                color: "var(--mly-ink-900)",
                letterSpacing: "-0.02em",
                lineHeight: 1,
              }}
            >
              {selected.length}
            </span>
            <span style={{ fontSize: 13, color: "var(--mly-ink-500)" }}>
              / {mediaNetwork.length} 家
            </span>
          </div>
          <div
            style={{
              height: 6,
              background: "var(--mly-ink-050)",
              borderRadius: 999,
              overflow: "hidden",
              marginBottom: 14,
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${(selected.length / mediaNetwork.length) * 100}%`,
                background: "linear-gradient(90deg, var(--mly-teal-400), var(--mly-teal-700))",
                transition: "width 220ms",
              }}
            />
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 10,
              marginBottom: 14,
            }}
          >
            <div>
              <div
                style={{
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  color: "var(--mly-ink-500)",
                }}
              >
                每週觸及
              </div>
              <div
                style={{
                  fontFamily: "var(--font-numeric)",
                  fontSize: 20,
                  fontWeight: 700,
                  color: "var(--mly-teal-700)",
                  marginTop: 4,
                }}
              >
                <CountUp to={totalReach / 1_000_000} decimals={1} suffix="M" duration={400} />
              </div>
              <div
                style={{
                  fontSize: 10,
                  color: "var(--mly-ink-500)",
                  fontFamily: "var(--font-mono)",
                }}
              >
                讀者
              </div>
            </div>
            <div>
              <div
                style={{
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  color: "var(--mly-ink-500)",
                }}
              >
                Context Agents
              </div>
              <div
                style={{
                  fontFamily: "var(--font-numeric)",
                  fontSize: 20,
                  fontWeight: 700,
                  color: "var(--mly-teal-700)",
                  marginTop: 4,
                }}
              >
                {selected.length}
              </div>
              <div
                style={{
                  fontSize: 10,
                  color: "var(--mly-ink-500)",
                  fontFamily: "var(--font-mono)",
                }}
              >
                各自上線
              </div>
            </div>
          </div>

          {competitorList.length ? (
            <div
              style={{
                padding: 12,
                background: "var(--cortex-amber-50)",
                border: "1px solid var(--cortex-amber-200)",
                borderRadius: 6,
                fontSize: 12,
                color: "var(--mly-ink-800)",
                lineHeight: 1.55,
              }}
            >
              <Icon name="campaign" size={14} color="var(--cortex-amber-600)" />{" "}
              <strong>{competitorList.slice(0, 3).join("、")}</strong> 已在這幾家媒體本週合計出現{" "}
              <strong>286 次</strong>。
            </div>
          ) : null}
        </Card>
      </div>
    </div>
  );
}
