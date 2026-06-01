/**
 * Auto-play orchestrator for the demo wizard.
 *
 * Uses Vitest fake timers to advance through the 1.5s → 6s → 4s × 3 → 5s
 * cadence without taking 25s of wall clock. The test asserts only the
 * observable transitions (which step the wizard renders), not the timer
 * mechanics directly — so the durations are calibrated to "after the
 * scheduled pause has elapsed" rather than reproduced verbatim.
 */
import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  CRAWL_TASKS,
  DEPLOY_AGENTS,
  DEPLOY_LOG,
  EXTRACTED_BRAND,
  LIVE_QUESTIONS,
  MEDIA_NETWORK,
  VOICE_TONES,
} from "@/components/onboarding-v2/data";
import { OnboardingV2Wizard } from "@/components/onboarding-v2/wizard";
import type { OnboardingApi } from "@/lib/onboarding/api";

// The wizard transitively imports the post-onboarding interstitial, which pulls
// in a "use server" actions module (next-auth). Demo/autoplay never reach it,
// but the import must resolve in jsdom — mock it.
vi.mock("@/app/brand/dashboard/report-actions", () => ({
  consumeCelebrate: vi.fn().mockResolvedValue(undefined),
  loadReportState: vi.fn(() => new Promise(() => {})),
}));

// add-brand-actions is a "use server" file that imports next-auth server helpers
// (next-auth/lib/env.js → next/server). Stub it so the wizard renders in jsdom
// without pulling in server-only modules.
vi.mock("@/app/(auth)/onboarding/v2/add-brand-actions", () => ({
  listMyBrandsAction: vi.fn(async () => []),
  createAnotherBrandAction: vi.fn(async () => ({
    brandId: "test-brand-id",
    activeContext: { kind: "brand", id: "test-brand-id", role: "admin", capabilities: [] },
  })),
}));

function makeOkApi(): OnboardingApi {
  return {
    analyzeBrand: vi.fn(async () => EXTRACTED_BRAND),
    getCrawlTasks: vi.fn(async () => CRAWL_TASKS),
    getMediaNetwork: vi.fn(async () => MEDIA_NETWORK),
    getLiveQuestions: vi.fn(async () => LIVE_QUESTIONS),
    getVoiceTones: vi.fn(async () => VOICE_TONES),
    getDeployAgents: vi.fn(async () => DEPLOY_AGENTS),
    getDeployLog: vi.fn(async () => DEPLOY_LOG),
  };
}

/**
 * Advance fake timers AND flush React's microtask queue so state updates
 * scheduled by useState/useCallback inside a setTimeout callback actually
 * commit before the next assertion. `vi.advanceTimersByTimeAsync` does
 * both in one call; wrapping in `act` keeps Testing Library happy.
 */
async function flush(ms: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

beforeEach(() => {
  vi.useFakeTimers();
  window.localStorage.clear();
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe("OnboardingV2Wizard — autoPlay", () => {
  it("does NOT auto-advance when autoPlay is false", async () => {
    render(<OnboardingV2Wizard mode="demo" api={makeOkApi()} />);
    // Mount loads modeled scaffolding asynchronously; flush microtasks
    // without advancing any timer-based transitions.
    await flush(0);
    expect(
      screen.getByRole("button", { name: /analyze my brand/i }),
    ).toBeInTheDocument();

    // Plenty of wall clock — but no autoPlay timers were ever scheduled,
    // so the wizard stays at step 0.
    await flush(10_000);
    expect(
      screen.getByRole("button", { name: /analyze my brand/i }),
    ).toBeInTheDocument();
  });

  it("auto-advances step 0 → step 1 (crawl) after 1.5s", async () => {
    render(
      <OnboardingV2Wizard mode="demo" api={makeOkApi()} autoPlay={true} />,
    );
    // Step 0 visible before the timer fires.
    expect(
      screen.getByRole("button", { name: /analyze my brand/i }),
    ).toBeInTheDocument();

    // Just past 1.5s: orchestrator fires onAnalyze + setStep(1). The
    // crawl screen takes over.
    await flush(1_600);
    expect(
      screen.queryByRole("button", { name: /analyze my brand/i }),
    ).not.toBeInTheDocument();
  });

  it("does NOT auto-advance when mode is live (autoPlay only applies to demo)", async () => {
    render(
      <OnboardingV2Wizard
        mode="live"
        api={makeOkApi()}
        onComplete={vi.fn(async () => {})}
        autoPlay={true}
      />,
    );
    expect(
      screen.getByRole("button", { name: /analyze my brand/i }),
    ).toBeInTheDocument();

    // Even with autoPlay=true, live mode ignores it. Step 0 stays put.
    await flush(10_000);
    expect(
      screen.getByRole("button", { name: /analyze my brand/i }),
    ).toBeInTheDocument();
  });
});
