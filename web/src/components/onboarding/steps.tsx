/**
 * Onboarding step bodies — five mutually-exclusive panels.
 *
 * Each step receives `draft` (read) and `onChange` (write). The wizard owns
 * the draft state and the navigation; these components only describe their
 * own form fields. Per design handoff §04 the heading uses the same H2
 * shape across all 5 steps with a teal-700 accent on the variable noun.
 */

import { Input } from "@/components/ui/input";
import type { OnboardingDraft } from "@/lib/mock-session";
import { INDUSTRIES, type Industry } from "@/lib/onboarding";
import { cn } from "@/lib/utils";

export interface StepProps {
  draft: OnboardingDraft;
  onChange: (patch: Partial<OnboardingDraft>) => void;
}

function StepHeading({
  prefix,
  highlight,
  caption,
}: {
  prefix: string;
  highlight: string;
  caption: string;
}) {
  return (
    <>
      <h2
        className="mt-2 mb-3"
        style={{
          font: "700 36px/1.15 var(--font-sans)",
          letterSpacing: "-0.02em",
        }}
      >
        {prefix}{" "}
        <span style={{ color: "var(--mly-teal-700)" }}>{highlight}</span>
      </h2>
      <p className="mb-7 text-sm text-ink-500">{caption}</p>
    </>
  );
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <label className="mb-1.5 block text-[11px] font-bold uppercase tracking-[0.06em] text-ink-600">
      {children}
    </label>
  );
}

// ---------------------------------------------------------------------------
// Step 1 — Company
// ---------------------------------------------------------------------------

export function StepCompany({ draft, onChange }: StepProps) {
  return (
    <>
      <StepHeading
        prefix="Tell us about your"
        highlight="company."
        caption="Used everywhere in the product. The short name appears in tight spaces (sidebar, breadcrumbs)."
      />
      <div className="flex flex-col gap-5">
        <div>
          <FieldLabel>Company name</FieldLabel>
          <Input
            value={draft.companyName ?? ""}
            onChange={(e) => onChange({ companyName: e.target.value })}
            placeholder="Acme Bank Asia"
            autoFocus
          />
        </div>
        <div>
          <FieldLabel>Short name (optional)</FieldLabel>
          <Input
            value={draft.shortName ?? ""}
            onChange={(e) => onChange({ shortName: e.target.value })}
            placeholder="Acme"
          />
        </div>
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Step 2 — Domain
// ---------------------------------------------------------------------------

export function StepDomain({ draft, onChange }: StepProps) {
  return (
    <>
      <StepHeading
        prefix="What's your"
        highlight="primary domain?"
        caption="Cortex tracks brand visibility against this domain in AI surfaces. Add alt domains if you operate on more than one host."
      />
      <div className="flex flex-col gap-5">
        <div>
          <FieldLabel>Primary domain</FieldLabel>
          <Input
            value={draft.primaryDomain ?? ""}
            onChange={(e) => onChange({ primaryDomain: e.target.value })}
            placeholder="acmebank.asia"
            autoFocus
            spellCheck={false}
          />
        </div>
        <div>
          <FieldLabel>Alt domains (optional, comma-separated)</FieldLabel>
          <Input
            value={draft.altDomains ?? ""}
            onChange={(e) => onChange({ altDomains: e.target.value })}
            placeholder="acmebank.com, acme-bank.tw"
            spellCheck={false}
          />
        </div>
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Step 3 — Industry chip select
// ---------------------------------------------------------------------------

export function StepIndustry({ draft, onChange }: StepProps) {
  return (
    <>
      <StepHeading
        prefix="What's your"
        highlight="industry?"
        caption="Drives publisher recommendations during placement matching. Editable later in Settings."
      />
      <div className="grid grid-cols-3 gap-2">
        {INDUSTRIES.map((opt) => {
          const active = draft.industry === opt;
          return (
            <button
              key={opt}
              type="button"
              onClick={() => onChange({ industry: opt as Industry })}
              className={cn(
                "rounded-sm py-3 text-sm transition-colors duration-state ease-std",
                active
                  ? "border-2 border-brand-600 bg-brand-50 font-medium text-brand-700"
                  : "border border-ink-200 bg-white hover:border-ink-300",
              )}
            >
              {opt}
            </button>
          );
        })}
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Step 4 — Primary contact
// ---------------------------------------------------------------------------

export function StepContact({ draft, onChange }: StepProps) {
  return (
    <>
      <StepHeading
        prefix="Who's the"
        highlight="primary contact?"
        caption="Receives onboarding emails, alerts, and the monthly Cortex digest. Should be a work email at your domain."
      />
      <div className="flex flex-col gap-5">
        <div>
          <FieldLabel>Full name</FieldLabel>
          <Input
            value={draft.contactName ?? ""}
            onChange={(e) => onChange({ contactName: e.target.value })}
            placeholder="王小明"
            autoFocus
          />
        </div>
        <div>
          <FieldLabel>Title</FieldLabel>
          <Input
            value={draft.contactTitle ?? ""}
            onChange={(e) => onChange({ contactTitle: e.target.value })}
            placeholder="CMO"
          />
        </div>
        <div>
          <FieldLabel>Work email</FieldLabel>
          <Input
            type="email"
            value={draft.contactEmail ?? ""}
            onChange={(e) => onChange({ contactEmail: e.target.value })}
            placeholder="ming@acmebank.asia"
            spellCheck={false}
          />
        </div>
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Step 5 — Placement preferences
// ---------------------------------------------------------------------------

export function StepPlacement({ draft, onChange }: StepProps) {
  return (
    <>
      <StepHeading
        prefix="Where should your brand"
        highlight="show up?"
        caption="Free-text guidance for the placement team. Topics, audiences, or publisher tiers — describe what you'd say to a media planner."
      />

      <div className="mb-5 flex flex-col gap-5">
        <div>
          <FieldLabel>Topics in (we want)</FieldLabel>
          <textarea
            value={draft.placementTopicsIn ?? ""}
            onChange={(e) =>
              onChange({ placementTopicsIn: e.target.value })
            }
            placeholder="Personal finance · credit cards · airline miles · wealth management"
            rows={3}
            className="w-full resize-y rounded-sm border border-ink-200 bg-white px-[14px] py-2.5 text-sm text-ink-800 placeholder:text-ink-400 focus:border-2 focus:border-brand-800 focus:px-[13px] focus:py-[9px] focus:outline-none focus:shadow-[var(--focus-ring)]"
          />
        </div>
        <div>
          <FieldLabel>Topics out (avoid)</FieldLabel>
          <textarea
            value={draft.placementTopicsOut ?? ""}
            onChange={(e) =>
              onChange({ placementTopicsOut: e.target.value })
            }
            placeholder="Cryptocurrency speculation · payday lending · gambling-adjacent"
            rows={3}
            className="w-full resize-y rounded-sm border border-ink-200 bg-white px-[14px] py-2.5 text-sm text-ink-800 placeholder:text-ink-400 focus:border-2 focus:border-brand-800 focus:px-[13px] focus:py-[9px] focus:outline-none focus:shadow-[var(--focus-ring)]"
          />
        </div>
      </div>

      <div
        className="rounded-sm border border-amber-200 bg-amber-50 px-4 py-3.5 text-[13px] leading-relaxed text-ink-800"
        style={{ borderLeft: "3px solid var(--cortex-amber-500)" }}
      >
        <strong>Heads up.</strong> Actual placement matching is done by Mlytics
        ops manually — these preferences are <strong>advisory only</strong>{" "}
        for v1.
      </div>
    </>
  );
}
