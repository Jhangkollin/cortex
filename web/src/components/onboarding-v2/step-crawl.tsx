"use client";

/**
 * Step 1B — Crawl animation.
 *
 * Two-column layout: faux browser preview on the left with an amber scan-line
 * sweeping the page and a highlight box jumping to whichever section the
 * crawler is currently "reading"; on the right, the task checklist and the
 * "what we found" counters tick up as each phase completes.
 */

import { useEffect, useRef, useState } from "react";

import type { CrawlTask, ExtractedBrand } from "./data";
import { Badge, Card, CountUp, Icon, OnbButton } from "./primitives";

type Highlight = { y: number; h: number; label: string } | null;

const HIGHLIGHTS: Record<string, Highlight> = {
  fetch: null,
  meta: { y: 8, h: 38, label: "<head>" },
  logo: { y: 54, h: 44, label: "Logo" },
  products: { y: 240, h: 130, label: "Product grid" },
  category: { y: 96, h: 60, label: "Hero copy" },
  voice: { y: 396, h: 110, label: "About · Press" },
  competitors: null,
  done: null,
};

const NAV_LINKS = ["Personal", "Business", "Investing", "About us"];

// Pacing knob: each crawl phase lingers ~1.5x its base delay so the step
// stays readable without dragging, and the screen parks on a manual
// "Continue" button instead of auto-jumping straight into brand review.
const PACE = 1.5;

export function StepCrawl({
  url,
  ready,
  brand,
  onComplete,
  crawlTasks,
}: {
  url: string;
  /**
   * True once the real analyze has resolved (brand profile available).
   * The scripted scan animation typically finishes before the ~25s
   * extraction; until `ready`, the end card stays in a "still scanning"
   * state and the Continue CTA is disabled rather than dead-clicking.
   */
  ready: boolean;
  /**
   * The real extracted brand once analyze resolves; `null` while still
   * scanning. Drives the faux-browser preview + "Found" counters so they
   * reflect the actual site instead of the hardcoded Acme Bank mock.
   */
  brand: ExtractedBrand | null;
  onComplete: () => void;
  crawlTasks: CrawlTask[];
}) {
  const [taskIdx, setTaskIdx] = useState(0);
  const crawlDone = taskIdx >= crawlTasks.length;

  // The real extracted brand, available only once analyze resolves
  // (`ready`). `b` narrows for TS so the faux-browser preview + the
  // "Found" counters can render the real fetched values instead of the
  // hardcoded Acme Bank mock; while scanning (`b == null`) we show a
  // neutral skeleton tied to the URL being read, not a fake brand.
  const b: ExtractedBrand | null = ready ? brand : null;
  const host = url.replace(/^https?:\/\//, "").replace(/\/+$/, "").split("/")[0];

  // Decouple the crawl timer from `crawlTasks` array-reference identity.
  // The mock adapter returns the same module-level constant every call, but
  // the real HttpOnboardingApi (SP-3a) will allocate a fresh array per fetch
  // with identical content. If the effect depended on the array reference, a
  // coincident refetch would tear down the in-flight tick and stall the
  // animation. Capture the per-step delays once so the timer reads them from
  // a stable source and the effect can depend on primitives only.
  const delaysRef = useRef<number[]>(crawlTasks.map((t) => t.delay));

  useEffect(() => {
    if (crawlDone) return; // finished — wait for the user to click Continue
    const t = setTimeout(
      () => setTaskIdx((i) => i + 1),
      delaysRef.current[taskIdx] * PACE,
    );
    return () => clearTimeout(t);
  }, [taskIdx, crawlDone]);

  const currentTaskId = crawlTasks[Math.min(taskIdx, crawlTasks.length - 1)].id;
  const hi = HIGHLIGHTS[currentTaskId];

  return (
    <div>
      <Badge color="amber" style={{ marginBottom: 12 }}>
        Step 1 · Analyzing
      </Badge>
      <h2
        style={{
          fontSize: 26,
          fontWeight: 700,
          color: "var(--mly-ink-900)",
          letterSpacing: "-0.015em",
          marginBottom: 6,
          margin: 0,
        }}
      >
        Reading{" "}
        <span
          style={{
            fontFamily: "var(--font-mono)",
            color: "var(--mly-teal-700)",
            background: "var(--mly-teal-050)",
            padding: "2px 8px",
            borderRadius: 4,
          }}
        >
          {url}
        </span>
      </h2>
      <p style={{ color: "var(--mly-ink-600)", fontSize: 14, margin: "6px 0 24px" }}>
        This usually takes 60–90 seconds. Watch what Cortex picks up below.
      </p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1.4fr 1fr",
          gap: 18,
          alignItems: "flex-start",
        }}
      >
        {/* Mock browser preview with highlight overlays */}
        <Card style={{ padding: 0, overflow: "hidden" }}>
          {/* browser chrome */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "10px 14px",
              borderBottom: "1px solid var(--mly-ink-100)",
              background: "var(--mly-ink-025)",
            }}
          >
            <div style={{ display: "flex", gap: 5 }}>
              <span style={{ width: 11, height: 11, borderRadius: "50%", background: "#FF5F57" }} />
              <span style={{ width: 11, height: 11, borderRadius: "50%", background: "#FEBC2E" }} />
              <span style={{ width: 11, height: 11, borderRadius: "50%", background: "#28C840" }} />
            </div>
            <div
              style={{
                marginLeft: 12,
                flex: 1,
                padding: "5px 12px",
                borderRadius: 6,
                background: "#fff",
                border: "1px solid var(--mly-ink-150)",
                fontFamily: "var(--font-mono)",
                fontSize: 11,
                color: "var(--mly-ink-600)",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <Icon name="lock" size={11} color="var(--mly-success)" />
              https://{url}
            </div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 5,
                fontSize: 11,
                color: "var(--mly-success)",
                fontWeight: 600,
              }}
            >
              <span
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: "50%",
                  background: "var(--mly-success)",
                  animation: "mly-pulse 1s infinite",
                }}
              />
              LIVE
            </div>
          </div>

          {/* Faux website body */}
          <div style={{ position: "relative", height: 540, overflow: "hidden", background: "#fff" }}>
            {/* nav */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 18,
                padding: "16px 24px",
                borderBottom: "1px solid var(--mly-ink-100)",
              }}
            >
              <div
                style={{
                  width: 30,
                  height: 30,
                  borderRadius: 6,
                  background: b?.brandColor || "var(--mly-teal-700)",
                  color: "#fff",
                  display: "grid",
                  placeItems: "center",
                  fontWeight: 700,
                  fontSize: 14,
                }}
              >
                {b
                  ? b.monogram || b.name.charAt(0) || "•"
                  : host.charAt(0).toUpperCase() || "•"}
              </div>
              <div style={{ fontSize: 14, fontWeight: 700, color: "var(--mly-ink-900)" }}>
                {b ? b.name : host}
              </div>
              <div
                style={{
                  marginLeft: 16,
                  display: "flex",
                  gap: 14,
                  fontSize: 12,
                  color: "var(--mly-ink-600)",
                }}
              >
                {NAV_LINKS.map((l) => (
                  <span key={l}>{l}</span>
                ))}
              </div>
              <div
                style={{
                  marginLeft: "auto",
                  padding: "5px 14px",
                  borderRadius: 4,
                  background: "var(--mly-teal-700)",
                  color: "#fff",
                  fontSize: 11,
                  fontWeight: 600,
                }}
              >
                Sign in
              </div>
            </div>
            {/* hero */}
            <div style={{ padding: "24px 24px 18px" }}>
              <div
                style={{
                  fontSize: 22,
                  fontWeight: 700,
                  color: "var(--mly-ink-900)",
                  lineHeight: 1.3,
                  marginBottom: 6,
                }}
              >
                {b ? (
                  b.tagline || b.name
                ) : (
                  <span
                    style={{
                      display: "inline-block",
                      width: "62%",
                      height: 22,
                      borderRadius: 4,
                      background: "var(--mly-ink-100)",
                    }}
                  />
                )}
              </div>
              <div style={{ fontSize: 12, color: "var(--mly-ink-500)", lineHeight: 1.5 }}>
                {b ? (
                  [b.category?.value, b.region?.length ? b.region.join(", ") : null]
                    .filter(Boolean)
                    .join(" · ")
                ) : (
                  <span
                    style={{
                      display: "inline-block",
                      width: "40%",
                      height: 11,
                      borderRadius: 4,
                      background: "var(--mly-ink-100)",
                    }}
                  />
                )}
              </div>
            </div>
            {/* product grid */}
            <div style={{ padding: "0 24px" }}>
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  color: "var(--mly-ink-500)",
                  marginBottom: 8,
                }}
              >
                Featured products
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
                {Array.from({ length: 6 }).map((_, i) => {
                  const pname = b ? b.products[i]?.name : undefined;
                  // Real mode: render only the products actually extracted.
                  // Scanning mode (b == null): six neutral skeleton tiles.
                  if (b && !pname) return null;
                  return (
                    <div
                      key={i}
                      style={{
                        padding: 10,
                        borderRadius: 6,
                        background: "var(--mly-ink-025)",
                        border: "1px solid var(--mly-ink-100)",
                      }}
                    >
                      <div
                        style={{
                          width: 22,
                          height: 22,
                          borderRadius: 4,
                          background: "var(--mly-teal-050)",
                          marginBottom: 6,
                        }}
                      />
                      {pname ? (
                        <div style={{ fontSize: 12, fontWeight: 600, color: "var(--mly-ink-900)" }}>
                          {pname}
                        </div>
                      ) : (
                        <span
                          style={{
                            display: "block",
                            width: "70%",
                            height: 11,
                            borderRadius: 4,
                            background: "var(--mly-ink-100)",
                          }}
                        />
                      )}
                      {pname ? (
                        <div
                          style={{
                            fontSize: 10,
                            color: "var(--mly-ink-400)",
                            marginTop: 2,
                          }}
                        >
                          Learn more →
                        </div>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            </div>
            {/* about */}
            <div style={{ padding: "18px 24px" }}>
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  color: "var(--mly-ink-500)",
                  marginBottom: 6,
                }}
              >
                About {b ? b.name : host}
              </div>
              <div style={{ fontSize: 12, color: "var(--mly-ink-700)", lineHeight: 1.65 }}>
                {b ? (
                  b.about
                ) : (
                  <>
                    <span
                      style={{
                        display: "block",
                        width: "100%",
                        height: 10,
                        borderRadius: 4,
                        background: "var(--mly-ink-100)",
                        marginBottom: 6,
                      }}
                    />
                    <span
                      style={{
                        display: "block",
                        width: "92%",
                        height: 10,
                        borderRadius: 4,
                        background: "var(--mly-ink-100)",
                        marginBottom: 6,
                      }}
                    />
                    <span
                      style={{
                        display: "block",
                        width: "68%",
                        height: 10,
                        borderRadius: 4,
                        background: "var(--mly-ink-100)",
                      }}
                    />
                  </>
                )}
              </div>
            </div>

            {/* scan line animation */}
            <div
              aria-hidden
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                top: 0,
                height: 2,
                background:
                  "linear-gradient(90deg, transparent, var(--cortex-amber-500), transparent)",
                animation: "mly-scan-line 4s linear infinite",
                boxShadow: "0 0 14px var(--cortex-amber-500)",
                opacity: taskIdx < crawlTasks.length - 1 ? 0.65 : 0,
                transition: "opacity 200ms",
              }}
            />

            {/* highlight box for current focus */}
            {hi ? (
              <div
                aria-hidden
                style={{
                  position: "absolute",
                  left: 16,
                  right: 16,
                  top: hi.y,
                  height: hi.h,
                  border: "1.5px solid var(--cortex-amber-500)",
                  background: "rgba(245,158,11,0.10)",
                  borderRadius: 4,
                  transition: "all 350ms cubic-bezier(0.4,0,0.2,1)",
                  pointerEvents: "none",
                }}
              >
                <div
                  style={{
                    position: "absolute",
                    top: -22,
                    left: -1,
                    padding: "2px 8px",
                    borderRadius: 4,
                    background: "var(--cortex-amber-500)",
                    color: "var(--mly-ink-900)",
                    fontSize: 10,
                    fontWeight: 700,
                    letterSpacing: "0.04em",
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  ● {hi.label}
                </div>
              </div>
            ) : null}
          </div>
        </Card>

        {/* Task list */}
        <div>
          <Card style={{ padding: 18 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
              <div
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: "50%",
                  border: "2px solid var(--mly-teal-200)",
                  borderTopColor: "var(--mly-teal-700)",
                  animation: "mly-radar-sweep 0.6s linear infinite",
                }}
              />
              <div style={{ fontSize: 13, fontWeight: 700, color: "var(--mly-ink-900)" }}>
                What Cortex is doing
              </div>
              <span
                style={{
                  marginLeft: "auto",
                  fontSize: 11,
                  color: "var(--mly-ink-500)",
                  fontFamily: "var(--font-mono)",
                }}
              >
                {Math.min(taskIdx, crawlTasks.length)} / {crawlTasks.length}
              </span>
            </div>

            {/* Progress bar */}
            <div
              style={{
                height: 4,
                background: "var(--mly-ink-050)",
                borderRadius: 999,
                overflow: "hidden",
                marginBottom: 14,
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${(taskIdx / crawlTasks.length) * 100}%`,
                  background:
                    "linear-gradient(90deg, var(--mly-teal-400), var(--cortex-amber-500))",
                  transition: "width 360ms cubic-bezier(0.4,0,0.2,1)",
                }}
              />
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {crawlTasks.map((t, i) => {
                const done = i < taskIdx;
                const active = i === taskIdx;
                return (
                  <div
                    key={t.id}
                    style={{
                      display: "grid",
                      gridTemplateColumns: "26px 1fr auto",
                      gap: 10,
                      alignItems: "center",
                      padding: "8px 10px",
                      borderRadius: 6,
                      background: active ? "var(--mly-teal-050)" : "transparent",
                      opacity: i > taskIdx ? 0.4 : 1,
                      transition: "all 200ms",
                    }}
                  >
                    <div
                      style={{
                        width: 26,
                        height: 26,
                        borderRadius: 6,
                        background: done
                          ? "var(--mly-teal-050)"
                          : active
                            ? "#fff"
                            : "var(--mly-ink-050)",
                        border: `1px solid ${
                          done
                            ? "var(--mly-teal-200)"
                            : active
                              ? "var(--mly-teal-400)"
                              : "var(--mly-ink-150)"
                        }`,
                        display: "grid",
                        placeItems: "center",
                        color: done
                          ? "var(--mly-success)"
                          : active
                            ? "var(--mly-teal-700)"
                            : "var(--mly-ink-400)",
                      }}
                    >
                      {active ? (
                        <div
                          style={{
                            width: 10,
                            height: 10,
                            borderRadius: "50%",
                            border: "2px solid var(--mly-teal-200)",
                            borderTopColor: "var(--mly-teal-700)",
                            animation: "mly-radar-sweep 0.6s linear infinite",
                          }}
                        />
                      ) : (
                        <Icon name={done ? "check_circle" : t.icon} size={14} />
                      )}
                    </div>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: "var(--mly-ink-900)" }}>
                        {t.label}
                      </div>
                      <div
                        style={{
                          fontSize: 11,
                          color: "var(--mly-ink-500)",
                          fontFamily: "var(--font-mono)",
                          marginTop: 1,
                        }}
                      >
                        {t.detail}
                      </div>
                    </div>
                    <div
                      style={{
                        fontSize: 10,
                        fontWeight: 700,
                        fontFamily: "var(--font-mono)",
                        color: done
                          ? "var(--mly-success)"
                          : active
                            ? "var(--mly-teal-700)"
                            : "var(--mly-ink-300)",
                      }}
                    >
                      {done ? "OK" : active ? "…" : "—"}
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Findings counter */}
          <Card style={{ padding: 16, marginTop: 12 }}>
            <div
              style={{
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: "0.1em",
                textTransform: "uppercase",
                color: "var(--mly-ink-500)",
                marginBottom: 10,
              }}
            >
              Found
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 10 }}>
              {[
                // Real fetched counts once analyze resolves; 0 while
                // scanning (CountUp animates 0 → real on `ready`).
                // ExtractedBrand has no media field, so the old fictional
                // "Media matches" is replaced with the real "Regions".
                { l: "Products", v: b ? b.products.length : 0, i: "category" },
                { l: "Voice samples", v: b ? b.voiceSamples.length : 0, i: "campaign" },
                { l: "Competitors", v: b ? b.competitors.length : 0, i: "groups" },
                { l: "Regions", v: b ? b.region.length : 0, i: "hub" },
              ].map((s) => (
                <div key={s.l} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div
                    style={{
                      width: 28,
                      height: 28,
                      borderRadius: 6,
                      background: "var(--mly-ink-025)",
                      display: "grid",
                      placeItems: "center",
                    }}
                  >
                    <Icon
                      name={s.i}
                      size={14}
                      color={s.v > 0 ? "var(--mly-teal-700)" : "var(--mly-ink-300)"}
                    />
                  </div>
                  <div>
                    <div
                      style={{
                        fontFamily: "var(--font-numeric)",
                        fontWeight: 700,
                        fontSize: 18,
                        color: s.v > 0 ? "var(--mly-ink-900)" : "var(--mly-ink-300)",
                        lineHeight: 1,
                      }}
                    >
                      <CountUp to={s.v} duration={400} />
                    </div>
                    <div
                      style={{
                        fontSize: 10,
                        color: "var(--mly-ink-500)",
                        fontFamily: "var(--font-mono)",
                        marginTop: 2,
                      }}
                    >
                      {s.l}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {crawlDone ? (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 16,
            marginTop: 20,
            padding: "16px 18px",
            background: ready ? "var(--mly-teal-050)" : "var(--mly-ink-025)",
            border: `1px solid ${
              ready ? "var(--mly-teal-200)" : "var(--mly-ink-150)"
            }`,
            borderRadius: 10,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {ready ? (
              <Icon name="task_alt" size={20} color="var(--mly-success)" />
            ) : (
              <span
                aria-hidden
                style={{
                  width: 18,
                  height: 18,
                  borderRadius: "50%",
                  border: "2px solid var(--mly-ink-150)",
                  borderTopColor: "var(--mly-teal-700)",
                  animation: "mly-radar-sweep 0.8s linear infinite",
                  display: "inline-block",
                }}
              />
            )}
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: "var(--mly-ink-900)" }}>
                {ready ? "Analysis complete" : "Still scanning your site…"}
              </div>
              <div style={{ fontSize: 12, color: "var(--mly-ink-600)", marginTop: 2 }}>
                {ready
                  ? "Everything below is editable on the next step."
                  : "Reading pages and extracting your brand profile — this can take up to a minute."}
              </div>
            </div>
          </div>
          <OnbButton
            variant="primary"
            size="lg"
            iconRight="arrow_forward"
            disabled={!ready}
            onClick={onComplete}
          >
            {ready ? "Continue · Confirm brand" : "Analyzing…"}
          </OnbButton>
        </div>
      ) : null}
    </div>
  );
}
