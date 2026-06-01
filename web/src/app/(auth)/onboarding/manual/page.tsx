"use client";

/**
 * Brand onboarding wizard host (5 steps).
 *
 * URL contract: /onboarding/manual?step=N where N ∈ [1..5]. Out-of-range
 * falls back to step 1 — bookmarking step 7 should not produce a broken page.
 *
 * State flow:
 *   - Each field write merges into the mock-session draft (so reloading the
 *     wizard resumes where you left off).
 *   - Continue runs `validateStep(...)`. On error, render under the form;
 *     on success, advance the step in the URL.
 *   - Final step's Continue calls `completeOnboarding(...)` and routes to
 *     the brand dashboard.
 *
 * Per design handoff §04 the rail is on the left and the form on the right
 * with a 64px gap; the top header has a Back button and a 160-wide progress
 * bar that fills proportional to step / 5.
 */

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useMemo, useState } from "react";

import { completeBrandOnboarding } from "@/app/(auth)/onboarding/manual/actions";
import { useMockSession } from "@/components/auth/mock-session-provider";
import { StepRail } from "@/components/onboarding/step-rail";
import {
  StepCompany,
  StepContact,
  StepDomain,
  StepIndustry,
  StepPlacement,
} from "@/components/onboarding/steps";
import { Button } from "@/components/ui/button";
import {
  parseStepParam,
  type StepIndex,
  validateStep,
} from "@/lib/onboarding";

function OnboardingInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const step = useMemo<StepIndex>(
    () => parseStepParam(searchParams.get("step")),
    [searchParams],
  );

  const { session, updateDraft, completeOnboarding } = useMockSession();
  const draft = session.onboardingDraft;

  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const goTo = (next: StepIndex) => {
    setError(null);
    router.push(`/onboarding/manual?step=${next}`);
  };

  const onContinue = async () => {
    const err = validateStep(step, draft);
    if (err) {
      setError(err);
      return;
    }
    if (step < 5) {
      goTo((step + 1) as StepIndex);
      return;
    }
    // Final step: PATCH the user's brand with the schema-backed wizard
    // fields (display_name / industry / domain). Other draft fields stay
    // in mock-session until a brand_profile table lands.
    setBusy(true);
    setError(null);
    try {
      const { brandDisplayName } = await completeBrandOnboarding(draft);
      // Keep the mock-session org name in sync so the topbar avatar /
      // greeting reflects the renamed brand without a hard reload.
      completeOnboarding({
        name: brandDisplayName,
        tier: "enterprise",
      });
      router.push("/brand/dashboard");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save brand info.");
    } finally {
      // Reset on every exit path (success OR error). Happy-path moot
      // because we navigate away, but if router.push ever throws or is
      // intercepted, the wizard won't get stuck at "Saving…" forever.
      setBusy(false);
    }
  };

  const onBack = () => {
    if (step === 1) return;
    goTo((step - 1) as StepIndex);
  };

  return (
    <div className="flex min-h-screen flex-col bg-ink-25">
      {/* Top header */}
      <header className="flex items-center justify-between border-b border-ink-150 bg-white px-8 py-[18px]">
        <Button
          variant="ghost"
          size="sm"
          onClick={onBack}
          disabled={step === 1}
        >
          <span
            className="material-icons-outlined"
            style={{ fontSize: 16 }}
            aria-hidden
          >
            arrow_back
          </span>
          Back
        </Button>
        <div className="flex items-center gap-2.5 text-[11px] font-bold uppercase tracking-[0.08em] text-ink-500">
          STEP {step} / 5
          <div className="h-1 w-40 overflow-hidden rounded-full bg-ink-150">
            <div
              className="h-full bg-brand-600 transition-[width] duration-route ease-std"
              style={{ width: `${(step / 5) * 100}%` }}
            />
          </div>
        </div>
      </header>

      {/* Two-column body */}
      <main className="mx-auto grid w-full max-w-[1100px] flex-1 grid-cols-[280px_1fr] gap-16 px-8 py-12">
        <StepRail current={step} />

        <div className="max-w-[540px]">
          <div className="text-[11px] font-bold uppercase tracking-[0.08em] text-brand-700">
            STEP {step} OF 5
          </div>
          {step === 1 ? (
            <StepCompany draft={draft} onChange={updateDraft} />
          ) : null}
          {step === 2 ? (
            <StepDomain draft={draft} onChange={updateDraft} />
          ) : null}
          {step === 3 ? (
            <StepIndustry draft={draft} onChange={updateDraft} />
          ) : null}
          {step === 4 ? (
            <StepContact draft={draft} onChange={updateDraft} />
          ) : null}
          {step === 5 ? (
            <StepPlacement draft={draft} onChange={updateDraft} />
          ) : null}

          {error ? (
            <p className="mt-4 text-sm text-danger">{error}</p>
          ) : null}

          <div className="mt-9 flex justify-between">
            <Button
              variant="soft"
              onClick={onBack}
              disabled={step === 1 || busy}
            >
              <span
                className="material-icons-outlined"
                style={{ fontSize: 16 }}
                aria-hidden
              >
                arrow_back
              </span>
              Previous
            </Button>
            <Button onClick={() => void onContinue()} disabled={busy}>
              {step === 5 ? (busy ? "Saving…" : "Complete") : "Continue"}
              <span
                className="material-icons-outlined"
                style={{ fontSize: 16 }}
                aria-hidden
              >
                arrow_forward
              </span>
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function OnboardingPage() {
  // Next requires useSearchParams() consumers to be wrapped in <Suspense>
  // when statically rendered.
  return (
    <Suspense fallback={<div className="min-h-screen bg-ink-25" />}>
      <OnboardingInner />
    </Suspense>
  );
}
