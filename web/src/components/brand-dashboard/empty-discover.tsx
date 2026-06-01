"use client";

/**
 * Empty Discover — what a freshly-onboarded brand sees before any source
 * is connected. Per design handoff v1.1 §06b.
 *
 * Layout shape is identical to populated Discover (KPI grid → funnel slot
 * → prompt → agent grid) so the transition to populated is a content swap,
 * not a layout swap. The greeting + range toggle live in the parent page;
 * this component renders everything below them.
 *
 * One hero CTA banner (ink-900, two actions). All KPI cards render in
 * place with `—` values + "↗ Connect a source" link sub-line. Funnel is
 * skeletoned at canonical 100/60/38/14% with ink-100 bars and `—` numerals.
 * Cortex prompt is visible but disabled. Agent grid collapses to a single
 * full-width tile.
 *
 * v2 re-skin (Discover v2.0, plan Task R7 / spec decision 6): visual layer
 * only — ad-hoc hex/spacing/font-shorthands swapped for v2 design tokens
 * (`var(--mly-*)`, `var(--sp-*)`, `var(--r-*)`, `var(--text-*)`). Behavior,
 * props, data source, and the `connectedSourceCount===0 && !demo` gate (in
 * the parent page) are unchanged; no loading/error states (spec §8).
 */

import { useMockSession } from "@/components/auth/mock-session-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardPad } from "@/components/ui/card";

const KPI_LABELS = [
  "AI Surface Visibility",
  "Cited as Answer",
  "Buyer Intent Matched",
  "Cost per Qualified Lead",
] as const;

// Funnel skeleton bars at canonical heights from §06b spec frame.
const FUNNEL_SKELETON = [
  { label: "Widget Views", height: "100%" },
  { label: "Brand Clicks", height: "60%" },
  { label: "Answer Views", height: "38%" },
  { label: "CTA Clicks", height: "14%" },
] as const;

export function EmptyDiscover() {
  const { enableDemoData } = useMockSession();

  return (
    <>
      {/* Connect-source hero banner (ink-900) */}
      <div
        id="connect-source-hero"
        className="grid items-center scroll-mt-20 md:grid-cols-[1fr_auto]"
        style={{
          marginBottom: "var(--sp-4)",
          gap: "var(--sp-6)",
          borderRadius: "var(--r-lg)",
          padding: "var(--sp-7)",
          background: "var(--mly-ink-900)",
          color: "var(--mly-white)",
        }}
      >
        <div>
          <div
            style={{
              font: "var(--text-overline)",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              color: "var(--mly-teal-200)",
            }}
          >
            CONNECT A SOURCE TO LIGHT THIS UP
          </div>
          <h3
            style={{
              marginTop: "var(--sp-2)",
              marginBottom: "var(--sp-1)",
              color: "var(--mly-white)",
              font: "var(--text-h2)",
              letterSpacing: "-0.015em",
            }}
          >
            Your KPIs are ready. Your data isn&apos;t.
          </h3>
          <p
            className="m-0 max-w-[560px]"
            style={{
              font: "var(--text-body)",
              color: "var(--mly-teal-200)",
            }}
          >
            Plug in GA4 or your CMS and Cortex backfills the past 30 days
            within five minutes. Or load demo data to walk the product first —
            you can swap in real sources later from Connectors.
          </p>
        </div>
        <div
          className="flex min-w-[220px] flex-col"
          style={{ gap: "var(--sp-2)" }}
        >
          {/* Primary action — amber-on-ink-900 is the only place amber sits
              on dark per the design system. Per §06b the click should route
              to /connectors; for the skeleton we route there directly. */}
          <Button
            asChild
            style={{
              background: "var(--cortex-amber-500)",
              borderColor: "var(--cortex-amber-500)",
              color: "var(--mly-ink-900)",
            }}
          >
            <a href="/connectors">
              <span
                className="material-icons-outlined"
                style={{ fontSize: 18 }}
                aria-hidden
              >
                hub
              </span>
              Connect a source
            </a>
          </Button>
          <Button
            variant="soft"
            onClick={enableDemoData}
            className="bg-transparent text-white hover:bg-white/10"
            style={{ borderColor: "rgba(255,255,255,0.25)" }}
          >
            <span
              className="material-icons-outlined"
              style={{ fontSize: 16 }}
              aria-hidden
            >
              dataset
            </span>
            Use demo data
          </Button>
        </div>
      </div>

      {/* KPI cards — em-dash values, sub-line link to hero.
          Cols clamp to 4 max for the reason described in page.tsx. */}
      <div
        className="grid"
        style={{
          marginBottom: "var(--sp-4)",
          gap: "var(--sp-3)",
          gridTemplateColumns: "repeat(min(4, var(--shell-kpi-cols)), 1fr)",
        }}
      >
        {KPI_LABELS.map((label) => (
          <Card key={label}>
            <CardPad>
              <div
                style={{
                  font: "var(--text-overline)",
                  textTransform: "uppercase",
                  letterSpacing: "0.1em",
                  color: "var(--mly-ink-500)",
                }}
              >
                {label}
              </div>
              <div
                className="font-numeric font-bold"
                style={{
                  marginTop: "var(--sp-2)",
                  marginBottom: "var(--sp-1)",
                  fontSize: 36,
                  lineHeight: 1.1,
                  color: "var(--fg-subtle)",
                }}
              >
                —
              </div>
              <a
                href="#connect-source-hero"
                className="font-medium no-underline"
                style={{
                  font: "var(--text-strong)",
                  color: "var(--mly-teal-700)",
                }}
              >
                ↗ Connect a source
              </a>
            </CardPad>
          </Card>
        ))}
      </div>

      {/* Funnel skeleton */}
      <Card style={{ marginBottom: "var(--sp-4)" }}>
        <CardPad>
          <div
            className="flex items-baseline justify-between"
            style={{ marginBottom: "var(--sp-4)", gap: "var(--sp-3)" }}
          >
            <h3
              className="m-0 font-bold leading-snug"
              style={{ font: "var(--text-h3)", color: "var(--fg-subtle)" }}
            >
              Brand Funnel · awaiting source
            </h3>
            <Badge variant="soon">Awaiting source</Badge>
          </div>
          <div
            className="grid grid-cols-4 items-end"
            style={{ height: 160, gap: "var(--sp-2)" }}
          >
            {FUNNEL_SKELETON.map((stage) => (
              <div
                key={stage.label}
                className="flex h-full flex-col justify-end"
                style={{ gap: "var(--sp-2)" }}
              >
                <div
                  className="flex items-center justify-center font-numeric font-bold"
                  style={{
                    height: stage.height,
                    borderTopLeftRadius: "var(--r-md)",
                    borderTopRightRadius: "var(--r-md)",
                    background: "var(--mly-ink-100)",
                    color: "var(--fg-subtle)",
                    fontSize: 22,
                  }}
                >
                  —
                </div>
                <div
                  className="text-center leading-snug"
                  style={{
                    font: "var(--text-micro)",
                    color: "var(--fg-subtle)",
                  }}
                >
                  <strong>{stage.label}</strong>
                </div>
              </div>
            ))}
          </div>
        </CardPad>
      </Card>

      {/* Cortex prompt — visible but disabled */}
      <div
        className="flex"
        style={{
          marginBottom: "var(--sp-8)",
          gap: "var(--sp-2)",
          opacity: 0.55,
          pointerEvents: "none",
        }}
      >
        <Card
          className="flex flex-1 items-center"
          style={{
            gap: "var(--sp-3)",
            padding: "14px var(--sp-4)",
          }}
        >
          <span
            className="material-icons-outlined"
            style={{ fontSize: 22, color: "var(--mly-ink-400)" }}
            aria-hidden
          >
            add
          </span>
          <input
            disabled
            placeholder="Connect a source to ask Cortex…"
            className="flex-1 border-0 bg-transparent placeholder:text-ink-400 focus:outline-none"
            style={{ font: "var(--text-body)", color: "var(--mly-ink-400)" }}
            aria-label="Cortex prompt (disabled)"
          />
          <Badge variant="soon">Awaiting source</Badge>
        </Card>
        <Button variant="soft" className="h-auto" style={{ paddingInline: "var(--sp-6)" }}>
          <span
            className="material-icons-outlined"
            style={{ fontSize: 18 }}
            aria-hidden
          >
            graphic_eq
          </span>
          Speak
        </Button>
      </div>

      {/* Agents header — copy switches to "unlocks once a source is connected" */}
      <div
        className="flex items-baseline justify-between"
        style={{ marginTop: "var(--sp-8)", marginBottom: "var(--sp-3)" }}
      >
        <div
          style={{
            font: "var(--text-overline)",
            textTransform: "uppercase",
            letterSpacing: "0.1em",
            color: "var(--mly-ink-500)",
          }}
        >
          AGENTS TUNED FOR YOU
        </div>
        <div
          className="font-mono"
          style={{ fontSize: 11, color: "var(--mly-ink-400)" }}
        >
          unlocks once a source is connected
        </div>
      </div>

      {/* Single full-width "Awaiting source" tile (collapse from 6-up) */}
      <Card className="border-dashed bg-white">
        <div
          className="grid grid-cols-[auto_1fr_auto] items-center"
          style={{ gap: "var(--sp-6)", padding: "var(--sp-8)" }}
        >
          <div
            aria-hidden
            className="grid h-14 w-14 place-items-center border border-brand-200"
            style={{
              borderRadius: "var(--r-md)",
              background: "var(--mly-teal-050)",
            }}
          >
            <span
              className="material-icons-outlined text-brand-700"
              style={{ fontSize: 28 }}
            >
              hub
            </span>
          </div>
          <div>
            <div
              className="font-bold"
              style={{ font: "var(--text-h4)", color: "var(--mly-ink-900)" }}
            >
              Awaiting source
            </div>
            <div
              className="leading-relaxed"
              style={{
                marginTop: "var(--sp-1)",
                font: "var(--text-body)",
                color: "var(--mly-ink-500)",
              }}
            >
              Brand Monitor, Audience Finder, Lead Pilot, Brand Embed, Sales
              Converter, and Custom Agent appear here once Cortex sees data.
              Five minutes after you connect, this row populates.
            </div>
          </div>
          <Button asChild>
            <a href="/connectors">
              <span
                className="material-icons-outlined"
                style={{ fontSize: 18 }}
                aria-hidden
              >
                add
              </span>
              Connect a source
            </a>
          </Button>
        </div>
      </Card>
    </>
  );
}
