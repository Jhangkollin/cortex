"use client";

/**
 * Step 6 — Deployment overlay (full-screen).
 *
 * Two halves: agents-grid on the left ticking each agent from waiting →
 * connecting → online; deploy log on the right streaming in 16 lines. Both
 * sit on the Light Edition cream-paper canvas (handoff §3.3). Progress bar
 * and central radar globe react together: gold while deploying, lime when
 * done. Then the user lands on a gold "查看 Brand Agent 已上線" button.
 */

import { useEffect, useRef, useState } from "react";

import type { DeployAgent, DeployLogLine, Media } from "./data";
import { Icon, OnbButton } from "./primitives";

// Pacing knob: stream the agent grid and deploy log ~3x slower so each
// line is readable, then park on a manual "View Brand Agent online"
// button instead of auto-handing off to the success screen.
const PACE = 3;
const AGENT_STEP_MS = 280 * PACE;
const LOG_STEP_MS = 220 * PACE;

export function LaunchOverlay({
  onDone,
  deployAgents,
  deployLog,
  mediaNetwork,
  autoPlay = false,
}: {
  onDone: () => void;
  deployAgents: DeployAgent[];
  deployLog: DeployLogLine[];
  mediaNetwork: Media[];
  /**
   * When true, auto-calls `onDone` after the internal deploy log animation
   * completes (replaces the manual "View Brand Agent online" CTA). Used by
   * the demo route's autoplay mode.
   */
  autoPlay?: boolean;
}) {
  const [agentIdx, setAgentIdx] = useState(0);
  const [logIdx, setLogIdx] = useState(0);
  const logRef = useRef<HTMLDivElement>(null);

  // Decouple the timer effects from array-reference identity.
  const agentCount = deployAgents.length;
  const logCount = deployLog.length;

  useEffect(() => {
    if (agentIdx >= agentCount) return;
    const t = setTimeout(() => setAgentIdx((i) => i + 1), AGENT_STEP_MS);
    return () => clearTimeout(t);
  }, [agentIdx, agentCount]);

  useEffect(() => {
    if (logIdx >= logCount) return; // finished — wait for the user
    const t = setTimeout(() => setLogIdx((i) => i + 1), LOG_STEP_MS);
    return () => clearTimeout(t);
  }, [logIdx, logCount]);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" });
  }, [logIdx]);

  const progress = Math.min(
    100,
    ((agentIdx / deployAgents.length) * 0.6 + (logIdx / deployLog.length) * 0.4) * 100,
  );
  const isFinishing = logIdx >= deployLog.length;

  // Auto-progress to step 7 once the deploy log finishes (demo autoplay).
  useEffect(() => {
    if (!autoPlay || !isFinishing) return;
    const t = setTimeout(() => onDone(), 1800);
    return () => clearTimeout(t);
  }, [autoPlay, isFinishing, onDone]);

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        // Light Edition (handoff §3.3): deep-teal radial → cream radial.
        background:
          "radial-gradient(circle at 50% 35%, var(--paper-highlight) 0%, var(--paper) 50%, var(--paper-warm) 100%)",
        backdropFilter: "blur(8px)",
        zIndex: 1000,
        display: "grid",
        placeItems: "center",
        overflow: "auto",
        padding: "40px 20px",
        color: "var(--paper-ink)",
      }}
    >
      <div style={{ width: "100%", maxWidth: 1300 }}>
        {/* Header — central radar indicator. */}
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <div
            style={{
              width: 80,
              height: 80,
              margin: "0 auto 18px",
              borderRadius: "50%",
              background: "radial-gradient(circle, #fff 30%, transparent 70%)",
              border: "1px solid var(--paper-border)",
              position: "relative",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                position: "absolute",
                inset: 0,
                borderRadius: "50%",
                background: `conic-gradient(from 0deg, ${
                  isFinishing ? "rgba(var(--lime-deep-rgb), 0.55)" : "rgba(var(--gold-rgb), 0.55)"
                }, transparent 38%)`,
                animation: `mly-radar-sweep ${isFinishing ? "2.4s" : "0.9s"} linear infinite`,
              }}
            />
            <div
              style={{
                position: "absolute",
                left: "50%",
                top: "50%",
                transform: "translate(-50%,-50%)",
                width: 22,
                height: 22,
                borderRadius: "50%",
                background: isFinishing ? "var(--lime-deep)" : "var(--gold)",
                boxShadow: `0 0 24px ${
                  isFinishing ? "rgba(var(--lime-deep-rgb), 0.55)" : "rgba(var(--gold-rgb), 0.55)"
                }`,
                transition: "all 400ms",
              }}
            />
          </div>
          {/* Status badge — gold-soft while deploying, lime-soft when done. */}
          <span
            style={{
              display: "inline-block",
              padding: "4px 10px",
              borderRadius: 999,
              background: isFinishing ? "var(--lime-soft)" : "var(--gold-soft)",
              color: isFinishing ? "var(--lime-deep)" : "var(--gold-deep)",
              border: `1px solid ${isFinishing ? "var(--lime-soft-border)" : "var(--gold-border)"}`,
              fontSize: 11,
              fontFamily: "var(--font-mono)",
              letterSpacing: "0.14em",
              textTransform: "uppercase",
              fontWeight: 700,
              marginBottom: 12,
            }}
          >
            {isFinishing ? "部署完成" : "正在部署"}
          </span>
          <h2
            style={{
              fontSize: 28,
              fontWeight: 700,
              letterSpacing: "-0.015em",
              marginBottom: 6,
              margin: 0,
              color: "var(--paper-ink)",
            }}
          >
            {isFinishing ? "Brand Agent 已上線" : "正在把工作分派出去…"}
          </h2>
          <div style={{ fontSize: 13, color: "var(--paper-ink-2)", marginTop: 6 }}>
            {deployAgents.length} 個 Agent · {mediaNetwork.length} 家媒體 · 即時連線中
          </div>
        </div>

        {/* Progress bar */}
        <div style={{ marginBottom: 22 }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 6,
              fontSize: 11,
              fontFamily: "var(--font-mono)",
              color: "var(--paper-ink-3)",
              fontWeight: 700,
            }}
          >
            <span>{Math.round(progress)}% 完成</span>
            <span>ETA · {isFinishing ? "就緒" : "~20s"}</span>
          </div>
          <div
            style={{
              height: 4,
              background: "var(--paper-border-soft)",
              borderRadius: 999,
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${progress}%`,
                background: isFinishing
                  ? "linear-gradient(90deg, var(--lime-deep), var(--brand-teal))"
                  : "linear-gradient(90deg, var(--brand-teal), var(--gold))",
                transition: "width 220ms ease-out, background 400ms",
                boxShadow: "0 0 10px rgba(var(--gold-rgb), 0.40)",
              }}
            />
          </div>
        </div>

        {/* Two-column dashboard */}
        <div style={{ display: "grid", gridTemplateColumns: "1.05fr 1fr", gap: 16 }}>
          {/* LEFT — Agents grid (white card, paper-border). */}
          <div
            style={{
              background: "#fff",
              border: "1px solid var(--paper-border)",
              borderRadius: 12,
              padding: 18,
              boxShadow: "0 6px 18px -6px rgba(var(--paper-ink-rgb), 0.10)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
              <Icon name="smart_toy" size={16} color="var(--brand-teal)" />
              <div
                style={{
                  fontSize: 12,
                  fontWeight: 700,
                  letterSpacing: "0.06em",
                  textTransform: "uppercase",
                  color: "var(--paper-ink)",
                }}
              >
                Agent 部署狀態
              </div>
              <span
                style={{
                  marginLeft: "auto",
                  fontSize: 11,
                  fontFamily: "var(--font-mono)",
                  color: "var(--paper-ink-3)",
                }}
              >
                {Math.min(agentIdx, deployAgents.length)} / {deployAgents.length}
              </span>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
              {deployAgents.map((a, i) => {
                const isOnline = i < agentIdx;
                const isConnecting = i === agentIdx;
                const isWaiting = i > agentIdx;
                const rowBg = isOnline
                  ? "var(--brand-teal-soft)"
                  : isConnecting
                    ? "var(--gold-soft)"
                    : "var(--ink-warm-50)";
                const rowBorder = isOnline
                  ? "var(--brand-teal-soft-border)"
                  : isConnecting
                    ? "var(--gold-border)"
                    : "var(--paper-border-soft)";
                const iconColor = isOnline
                  ? "var(--brand-teal)"
                  : isConnecting
                    ? "var(--gold)"
                    : "var(--paper-ink-3)";
                return (
                  <div
                    key={a.id}
                    style={{
                      display: "grid",
                      gridTemplateColumns: "auto 1fr auto",
                      gap: 8,
                      alignItems: "center",
                      padding: "8px 10px",
                      borderRadius: 6,
                      background: rowBg,
                      border: `1px solid ${rowBorder}`,
                      opacity: isWaiting ? 0.55 : 1,
                      transition: "all 220ms",
                      animation: isConnecting ? "mly-pop-in 280ms" : "none",
                    }}
                  >
                    <Icon name={a.icon} size={13} color={iconColor} />
                    <div style={{ minWidth: 0 }}>
                      <div
                        style={{
                          fontSize: 11,
                          fontWeight: 700,
                          color: "var(--paper-ink)",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {a.name}
                      </div>
                      <div
                        style={{
                          fontSize: 9,
                          fontFamily: "var(--font-mono)",
                          color: "var(--paper-ink-3)",
                          marginTop: 1,
                        }}
                      >
                        {isOnline
                          ? "● 已連線 · ap-tw-1"
                          : isConnecting
                            ? "○ 連線中…"
                            : "— 等候中"}
                      </div>
                    </div>
                    {isOnline ? (
                      <span
                        style={{
                          width: 6,
                          height: 6,
                          borderRadius: "50%",
                          background: "var(--lime-deep)",
                          boxShadow: "0 0 8px rgba(var(--lime-deep-rgb), 0.5)",
                        }}
                      />
                    ) : isConnecting ? (
                      <div
                        style={{
                          width: 10,
                          height: 10,
                          borderRadius: "50%",
                          border: "2px solid rgba(var(--gold-rgb), 0.3)",
                          borderTopColor: "var(--gold)",
                          animation: "mly-radar-sweep 0.6s linear infinite",
                        }}
                      />
                    ) : (
                      <span
                        style={{
                          width: 6,
                          height: 6,
                          borderRadius: "50%",
                          background: "var(--paper-border)",
                        }}
                      />
                    )}
                  </div>
                );
              })}
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, 1fr)",
                gap: 10,
                marginTop: 16,
                paddingTop: 14,
                borderTop: "1px solid var(--paper-border-soft)",
              }}
            >
              {[
                { l: "上下文代理", v: Math.min(agentIdx, 6), t: 6 },
                {
                  l: "核心代理",
                  v: Math.max(0, Math.min(agentIdx - 6, 4)),
                  t: 4,
                },
                {
                  l: "佇列任務",
                  v: agentIdx >= deployAgents.length ? 5 : 0,
                  t: 5,
                },
              ].map((s) => (
                <div key={s.l}>
                  <div
                    style={{
                      fontSize: 9,
                      fontFamily: "var(--font-mono)",
                      letterSpacing: "0.08em",
                      color: "var(--paper-ink-3)",
                      textTransform: "uppercase",
                      fontWeight: 700,
                    }}
                  >
                    {s.l}
                  </div>
                  <div
                    style={{
                      fontFamily: "var(--font-numeric)",
                      fontSize: 20,
                      fontWeight: 700,
                      color: "var(--paper-ink)",
                      marginTop: 2,
                    }}
                  >
                    {s.v}
                    <span
                      style={{
                        fontSize: 11,
                        color: "var(--paper-ink-3)",
                        fontWeight: 500,
                      }}
                    >
                      {" "}
                      / {s.t}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* RIGHT — Deploy log as a white "printout" card. */}
          <div
            style={{
              background: "#fff",
              border: "1px solid var(--paper-border)",
              borderRadius: 12,
              padding: 0,
              overflow: "hidden",
              display: "flex",
              flexDirection: "column",
              boxShadow: "0 6px 18px -6px rgba(var(--paper-ink-rgb), 0.10)",
            }}
          >
            <div
              style={{
                padding: "10px 14px",
                display: "flex",
                alignItems: "center",
                gap: 8,
                borderBottom: "1px dashed var(--paper-border)",
                background: "var(--ink-warm-50)",
              }}
            >
              <Icon name="receipt_long" size={16} color="var(--brand-teal)" />
              <span
                style={{
                  marginLeft: 4,
                  fontSize: 11,
                  fontFamily: "var(--font-mono)",
                  color: "var(--paper-ink-2)",
                  fontWeight: 700,
                  letterSpacing: "0.08em",
                }}
              >
                cortex@ap-tw-1 · deploy.log
              </span>
              <span
                style={{
                  marginLeft: "auto",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 5,
                  fontSize: 11,
                  color: isFinishing ? "var(--lime-deep)" : "var(--gold-deep)",
                  fontWeight: 700,
                  fontFamily: "var(--font-mono)",
                }}
              >
                <span
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: "currentColor",
                    animation: "mly-pulse 1.2s infinite",
                  }}
                />
                {isFinishing ? "完成" : "串流中"}
              </span>
            </div>
            <div
              ref={logRef}
              style={{
                padding: 14,
                fontFamily: "var(--font-mono)",
                fontSize: 11.5,
                lineHeight: 1.7,
                color: "var(--paper-ink)",
                height: 350,
                overflow: "auto",
              }}
            >
              {deployLog.slice(0, logIdx).map((line, i) => (
                <div
                  key={i}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "44px 1fr auto",
                    gap: 10,
                    animation: "mly-fade-up 240ms backwards",
                    paddingBottom: 2,
                  }}
                >
                  <span style={{ color: "var(--paper-ink-3)" }}>{line.t}</span>
                  <span
                    style={{
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      color: "var(--paper-ink-2)",
                    }}
                  >
                    {line.text}
                  </span>
                  <span
                    style={{
                      padding: "1px 6px",
                      borderRadius: 3,
                      background:
                        line.status === "DONE"
                          ? "var(--lime-soft)"
                          : "var(--brand-teal-soft)",
                      color:
                        line.status === "DONE"
                          ? "var(--lime-deep)"
                          : "var(--brand-teal)",
                      border: `1px solid ${
                        line.status === "DONE" ? "var(--lime-soft-border)" : "var(--brand-teal-soft-border)"
                      }`,
                      fontWeight: 700,
                      fontSize: 10,
                    }}
                  >
                    {line.status}
                  </span>
                </div>
              ))}
              {logIdx < deployLog.length ? (
                <div style={{ marginTop: 2, color: "var(--gold)" }}>
                  <span
                    style={{
                      display: "inline-block",
                      width: 8,
                      height: 12,
                      background: "var(--gold)",
                      verticalAlign: "middle",
                      animation: "mly-caret-blink 1s infinite",
                    }}
                  />
                </div>
              ) : (
                <div
                  style={{
                    marginTop: 8,
                    padding: "8px 0",
                    borderTop: "1px dashed var(--paper-border)",
                    color: "var(--lime-deep)",
                    fontWeight: 700,
                    textAlign: "center",
                  }}
                >
                  ▲ 部署完成 — Brand Agent 已上線
                </div>
              )}
            </div>
          </div>
        </div>

        {isFinishing ? (
          <div
            style={{
              marginTop: 22,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <OnbButton
              variant="gold"
              size="lg"
              iconRight="arrow_forward"
              onClick={onDone}
              glow="0 8px 18px -4px rgba(var(--gold-rgb), 0.45)"
              style={{ borderRadius: 7, fontWeight: 700 }}
            >
              查看 Brand Agent 已上線
            </OnbButton>
          </div>
        ) : null}
      </div>
    </div>
  );
}
