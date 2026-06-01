import type { OnboardingDraft } from "@/lib/mock-session";

/**
 * Onboarding wizard metadata + per-step validation.
 *
 * Five linear steps per design handoff §04. Each step holds:
 *   - title       — what shows in the left rail
 *   - validate    — pure check on the draft, returns first error or null
 *
 * Validators are intentionally tiny — zod was rejected as a dependency for
 * the skeleton. When real onboarding ships, swap to zod schemas in this
 * same shape. The wizard itself doesn't care.
 */

export type StepIndex = 1 | 2 | 3 | 4 | 5;

export const STEP_INDICES: readonly StepIndex[] = [1, 2, 3, 4, 5] as const;

export interface StepMeta {
  index: StepIndex;
  title: string;
}

export const STEPS: Record<StepIndex, StepMeta> = {
  1: { index: 1, title: "Company" },
  2: { index: 2, title: "Domain" },
  3: { index: 3, title: "Industry" },
  4: { index: 4, title: "Primary contact" },
  5: { index: 5, title: "Placement preferences" },
};

export const INDUSTRIES = [
  "Finance",
  "Fintech",
  "Insurance",
  "Wealth",
  "DTC",
  "Health",
  "Tech",
  "Auto",
  "Lifestyle",
] as const;

export type Industry = (typeof INDUSTRIES)[number];

// Domain shape — accepts standard registrable domains; not a TLD database,
// good enough for "is this a domain?" gate. Matches the prototype's expected
// values like "acmebank.asia".
const DOMAIN_RE = /^[a-z0-9-]+(\.[a-z0-9-]+)+$/i;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export type ValidationError = string | null;

export function validateStep(
  step: StepIndex,
  draft: OnboardingDraft,
): ValidationError {
  switch (step) {
    case 1: {
      if (!draft.companyName?.trim()) return "Company name is required.";
      return null;
    }
    case 2: {
      const dom = draft.primaryDomain?.trim();
      if (!dom) return "Primary domain is required.";
      if (!DOMAIN_RE.test(dom))
        return "Use a domain like acmebank.asia (no scheme, no path).";
      return null;
    }
    case 3: {
      if (!draft.industry) return "Pick one industry.";
      return null;
    }
    case 4: {
      if (!draft.contactName?.trim()) return "Contact name is required.";
      if (!draft.contactTitle?.trim()) return "Contact title is required.";
      const email = draft.contactEmail?.trim();
      if (!email) return "Contact email is required.";
      if (!EMAIL_RE.test(email)) return "Enter a valid work email address.";
      return null;
    }
    case 5: {
      // Free-text optional fields — always passes.
      return null;
    }
  }
}

/**
 * Parse a ?step=N URL param into a valid StepIndex, defaulting to 1.
 * Anything off-range falls back to 1 — we never want a wizard pointed
 * at a non-existent step.
 */
export function parseStepParam(raw: string | null): StepIndex {
  const n = Number(raw);
  if (Number.isInteger(n) && n >= 1 && n <= 5) return n as StepIndex;
  return 1;
}
