"use client";

/**
 * Step 7 — Onboarding complete.
 *
 * Not "you're ready" — "agents are online and doing work". Success badge with
 * a pulsing dot, 5 live agent cards, a row of Context Agents per outlet, four
 * numeric KPIs, and a teal hero CTA toward Discover that mentions the ETA on
 * the first batch of brand answers.
 *
 * Multi-brand variant (brands.length >= 2): swaps the hero copy to
 * "<Brand> joined your portfolio", renders a PortfolioBand, and adds a
 * secondary "Add a brand" CTA card alongside the primary "Enter Discover".
 */

import type { BrandListItem } from "@/lib/cortex-api";
import type { ExtractedBrand, Media } from "./data";
import { PortfolioBand } from "./portfolio-band";
import { Badge, Card, Icon, OnbButton } from "./primitives";

const LIVE_AGENTS: Array<{ name: string; icon: string; status: string; accent: "amber" | "teal" }> = [
  { name: "Answer Pilot", icon: "edit_note", status: "Drafting 3 answers", accent: "amber" },
  { name: "GEO Pilot", icon: "explore", status: "Calibrating distribution", accent: "teal" },
  { name: "Market Radar", icon: "radar", status: "Scanning competitors", accent: "teal" },
  { name: "Monetize Lens", icon: "insights", status: "Tracking attribution", accent: "teal" },
  { name: "Brand Voice", icon: "campaign", status: "Calibration complete", accent: "teal" },
];

function SecondaryAddBrandCta({ onClick, busy }: { onClick: () => void; busy?: boolean }) {
  return (
    <div className="rounded-md border border-ink-200 bg-white p-5">
      <div className="mb-2 inline-flex h-8 w-8 items-center justify-center rounded bg-ink-100">
        <span className="material-icons-outlined text-ink-700">library_add</span>
      </div>
      <div className="text-xs font-bold uppercase tracking-wide text-ink-500">Or, keep going</div>
      <div className="mt-1 text-xl font-bold text-ink-900">Onboard another brand</div>
      <div className="mt-1 text-sm text-ink-600">
        Manage subsidiaries, sub-brands, or client accounts side-by-side. Each one gets its own agent team.
      </div>
      <button
        type="button"
        onClick={onClick}
        disabled={busy}
        className="mt-4 inline-flex items-center gap-2 rounded-md border border-brand-700 bg-white px-4 py-2 text-sm font-bold text-brand-700 hover:bg-brand-50 disabled:opacity-60"
      >
        <span className="material-icons-outlined">add</span>
        {busy ? "Preparing…" : "Add a brand"}
      </button>
    </div>
  );
}

export function StepComplete({
  brand,
  pickedMedia,
  onRestart,
  onEnterDiscover,
  mediaNetwork,
  brands = [],
  justOnboardedBrandId,
  onAddBrand,
  addBrandBusy,
  addBrandError,
}: {
  brand: ExtractedBrand;
  pickedMedia: string[];
  onRestart: () => void;
  onEnterDiscover: () => void;
  mediaNetwork: Media[];
  brands?: BrandListItem[];
  justOnboardedBrandId?: string;
  onAddBrand?: () => void;
  addBrandBusy?: boolean;
  addBrandError?: string | null;
}) {
  const isMulti = brands.length >= 2;
  const productsOn = brand.products.filter((p) => p.picked).length;
  const mediaList = mediaNetwork.filter((m) => pickedMedia.includes(m.id));

  const kpis = [
    {
      l: "Queued tasks",
      v: "5",
      s: "High-intent this week",
      i: "list_alt",
      color: "var(--cortex-amber-600)",
    },
    {
      l: "Knowledge cards",
      v: String(productsOn),
      s: "Loaded into KB",
      i: "book",
      color: "var(--mly-teal-700)",
    },
    {
      l: "Est. monthly answers",
      v: String(productsOn * 18),
      s: "Answers / month",
      i: "edit_note",
      color: "var(--mly-ink-900)",
    },
    {
      l: "Est. monthly reach",
      v: "9.6M",
      s: "Readers",
      i: "visibility",
      color: "var(--mly-teal-700)",
    },
  ];

  return (
    <div style={{ paddingBottom: 80 }}>
      <div style={{ textAlign: "center", marginBottom: 30 }}>
        <div
          style={{
            width: 84,
            height: 84,
            margin: "0 auto 18px",
            borderRadius: "50%",
            background: "radial-gradient(circle, #E0F2F1 30%, var(--mly-teal-050) 80%)",
            border: "2px solid var(--mly-teal-200)",
            display: "grid",
            placeItems: "center",
            position: "relative",
            animation: "mly-pop-in 500ms cubic-bezier(0.4,0,0.2,1) both",
          }}
        >
          <Icon name="check_circle" size={46} color="var(--mly-success)" />
          <span
            aria-hidden
            style={{
              position: "absolute",
              top: -2,
              right: 2,
              width: 16,
              height: 16,
              borderRadius: "50%",
              background: "var(--mly-success)",
              border: "3px solid #fff",
              boxShadow: "0 0 14px var(--mly-success)",
              animation: "mly-pulse 1.5s infinite",
            }}
          />
        </div>
        <Badge color="success">
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: "currentColor",
              marginRight: 4,
              animation: "mly-pulse 1.4s infinite",
              display: "inline-block",
            }}
          />
          Brand Agent online
        </Badge>
        <h2
          style={{
            fontSize: 32,
            fontWeight: 700,
            color: "var(--mly-ink-900)",
            letterSpacing: "-0.015em",
            marginTop: 14,
            marginBottom: 8,
          }}
        >
          {isMulti
            ? <>{brand.name} joined your portfolio</>
            : <>{brand.name}&apos;s Agent is on the job</>}
        </h2>
        <p
          style={{
            color: "var(--mly-ink-600)",
            fontSize: 15,
            maxWidth: 580,
            margin: "0 auto",
            lineHeight: 1.55,
          }}
        >
          {isMulti ? (
            <>
              You now manage <strong style={{ color: "var(--mly-ink-900)" }}>{brands.length} brands</strong> from
              one Cortex workspace — switch between them anytime from the sidebar.
            </>
          ) : (
            <>
              First batch of Brand Answers expected{" "}
              <strong style={{ color: "var(--cortex-amber-600)" }}>~23h 47m</strong> from now.
              Head into Discover to see what Cortex has been working on.
            </>
          )}
        </p>
      </div>

      {/* Portfolio band — multi-brand only */}
      {isMulti && justOnboardedBrandId && onAddBrand ? (
        <PortfolioBand
          brands={brands}
          justOnboardedBrandId={justOnboardedBrandId}
          onAddBrand={onAddBrand}
          addBusy={addBrandBusy}
        />
      ) : null}

      {/* Live agent grid */}
      <Card style={{ padding: 18, marginBottom: 14 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: "var(--mly-success)",
              animation: "mly-pulse 1.4s infinite",
            }}
          />
          <div
            style={{
              fontSize: 12,
              fontWeight: 700,
              letterSpacing: "0.06em",
              textTransform: "uppercase",
              color: "var(--mly-ink-900)",
            }}
          >
            Live agents
          </div>
          <Badge color="success" style={{ marginLeft: "auto" }}>
            10 / 10 online
          </Badge>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 8 }}>
          {LIVE_AGENTS.map((a, i) => (
            <div
              key={a.name}
              style={{
                padding: 12,
                borderRadius: 8,
                background:
                  a.accent === "amber"
                    ? "linear-gradient(180deg, var(--cortex-amber-50), #fff 70%)"
                    : "#fff",
                border: `1px solid ${
                  a.accent === "amber" ? "var(--cortex-amber-200)" : "var(--mly-ink-150)"
                }`,
                animation: `mly-fade-up 300ms ${i * 60 + 200}ms backwards`,
                position: "relative",
              }}
            >
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 6,
                  background:
                    a.accent === "amber" ? "var(--cortex-amber-50)" : "var(--mly-teal-050)",
                  color:
                    a.accent === "amber" ? "var(--cortex-amber-600)" : "var(--mly-teal-700)",
                  display: "grid",
                  placeItems: "center",
                  marginBottom: 8,
                }}
              >
                <Icon name={a.icon} size={15} />
              </div>
              <div style={{ fontSize: 12, fontWeight: 700, color: "var(--mly-ink-900)" }}>
                {a.name}
              </div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 4,
                  marginTop: 4,
                  fontSize: 11,
                  color: "var(--mly-ink-600)",
                }}
              >
                <span
                  style={{
                    width: 5,
                    height: 5,
                    borderRadius: "50%",
                    background: "var(--mly-success)",
                    animation: "mly-pulse 1.6s infinite",
                  }}
                />
                {a.status}
              </div>
              <span
                style={{
                  position: "absolute",
                  top: 8,
                  right: 8,
                  fontSize: 9,
                  fontWeight: 700,
                  fontFamily: "var(--font-mono)",
                  color: "var(--mly-success)",
                  letterSpacing: "0.06em",
                }}
              >
                ● LIVE
              </span>
            </div>
          ))}
        </div>
      </Card>

      {/* Context Agents per media */}
      {mediaList.length > 0 ? (
        <Card style={{ padding: 18, marginBottom: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
            <Icon name="hub" size={16} color="var(--mly-teal-700)" />
            <div
              style={{
                fontSize: 12,
                fontWeight: 700,
                letterSpacing: "0.06em",
                textTransform: "uppercase",
                color: "var(--mly-ink-900)",
              }}
            >
              Context Agents · per outlet
            </div>
            <Badge color="teal" style={{ marginLeft: "auto" }}>
              {mediaList.length} online
            </Badge>
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: `repeat(${Math.min(mediaList.length, 6)}, 1fr)`,
              gap: 8,
            }}
          >
            {mediaList.map((m, i) => (
              <div
                key={m.id}
                style={{
                  padding: 12,
                  borderRadius: 8,
                  background: "var(--mly-ink-025)",
                  border: "1px solid var(--mly-ink-150)",
                  animation: `mly-fade-up 280ms ${i * 50 + 400}ms backwards`,
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
                  <div
                    style={{
                      width: 22,
                      height: 22,
                      borderRadius: 4,
                      background: "linear-gradient(135deg, var(--mly-teal-400), var(--mly-teal-700))",
                      color: "#fff",
                      display: "grid",
                      placeItems: "center",
                      fontWeight: 700,
                      fontSize: 11,
                      flexShrink: 0,
                    }}
                  >
                    {m.name.charAt(0)}
                  </div>
                  <span
                    style={{
                      width: 5,
                      height: 5,
                      borderRadius: "50%",
                      background: "var(--mly-success)",
                      animation: "mly-pulse 1.4s infinite",
                    }}
                  />
                </div>
                <div
                  style={{
                    fontSize: 11,
                    fontWeight: 600,
                    color: "var(--mly-ink-900)",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {m.name}
                </div>
                <div
                  style={{
                    fontSize: 9,
                    color: "var(--mly-ink-500)",
                    fontFamily: "var(--font-mono)",
                    marginTop: 2,
                  }}
                >
                  ● monitoring
                </div>
              </div>
            ))}
          </div>
        </Card>
      ) : null}

      {/* KPIs + Discover CTA */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 14 }}>
        {kpis.map((k) => (
          <Card key={k.l} style={{ padding: 14 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div
                style={{
                  width: 26,
                  height: 26,
                  borderRadius: 6,
                  background: "var(--mly-teal-050)",
                  display: "grid",
                  placeItems: "center",
                }}
              >
                <Icon name={k.i} size={14} color={k.color} />
              </div>
              <div
                style={{
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  color: "var(--mly-ink-500)",
                }}
              >
                {k.l}
              </div>
            </div>
            <div
              style={{
                fontFamily: "var(--font-numeric)",
                fontWeight: 700,
                fontSize: 26,
                color: k.color,
                marginTop: 8,
                lineHeight: 1.1,
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
          </Card>
        ))}
      </div>

      <div className={isMulti ? "grid grid-cols-1 gap-4 lg:grid-cols-2" : undefined}>
        {/* Light Edition (handoff §3.3): the "Enter Discover" hero card
            sheds its deep-teal gradient for a cream-paper one with
            paper-border, gold-soft icon backplate, and a gold solid CTA.
            "Start over" drops from onDark to the soft variant. */}
        <Card
          style={{
            padding: 22,
            background:
              "linear-gradient(135deg, var(--paper-highlight) 0%, var(--paper) 60%, var(--paper-warm) 100%)",
            color: "var(--paper-ink)",
            border: "1px solid var(--paper-border)",
            display: "grid",
            gridTemplateColumns: "auto 1fr auto",
            gap: 18,
            alignItems: "center",
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
              right: -60,
              top: -60,
              width: 220,
              height: 220,
              borderRadius: "50%",
              background: "conic-gradient(from 0deg, rgba(var(--gold-rgb), 0.22), transparent 28%)",
              animation: "mly-radar-sweep 6s linear infinite",
              // Decoration sits over the CTA buttons in the right column —
              // without pointer-events:none it eats clicks on "Enter Discover".
              pointerEvents: "none",
            }}
          />
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 12,
              position: "relative",
              background: "var(--gold-soft)",
              border: "1px solid var(--gold-border)",
              display: "grid",
              placeItems: "center",
            }}
          >
            <Icon name="explore" size={28} color="var(--gold)" />
          </div>
          <div>
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
              Next
            </div>
            <div
              style={{
                fontSize: 18,
                fontWeight: 700,
                marginBottom: 4,
                color: "var(--paper-ink)",
              }}
            >
              Open Discover to watch your Agents work
            </div>
            <div style={{ fontSize: 13, color: "var(--paper-ink-2)", lineHeight: 1.55 }}>
              Cortex pings you every day with what&apos;s new, what your agents are working on,
              and what to triage first.
            </div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <OnbButton variant="soft" size="md" icon="restart_alt" onClick={onRestart}>
              Start over
            </OnbButton>
            <OnbButton
              variant="gold"
              size="md"
              iconRight="arrow_forward"
              onClick={onEnterDiscover}
              glow="0 8px 18px -4px rgba(var(--gold-rgb), 0.45)"
              style={{ borderRadius: 7, fontWeight: 700 }}
            >
              Enter Discover
            </OnbButton>
          </div>
        </Card>
        {isMulti && onAddBrand ? (
          <>
            <SecondaryAddBrandCta onClick={onAddBrand} busy={addBrandBusy} />
            {addBrandError ? (
              <div className="mt-3 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">
                {addBrandError}
              </div>
            ) : null}
          </>
        ) : null}
      </div>
    </div>
  );
}
