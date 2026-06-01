/**
 * Demo-mode behaviour for the shared wizard. Pairs with wizard.live.test.tsx;
 * both files reuse the same makeOkApi helper-shape but test divergent
 * outcomes.
 */
import { fireEvent, render, screen } from "@testing-library/react";
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
import { router } from "@tests/helpers/session-mock-state";

// The wizard transitively imports the post-onboarding interstitial, which pulls
// in a "use server" actions module (next-auth). Demo mode never reaches it, but
// the import must resolve in jsdom — mock it.
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

afterEach(() => {
  vi.restoreAllMocks();
});

describe("OnboardingV2Wizard — mode='demo'", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("renders step 0 on mount even if the live completion flag is pre-set", async () => {
    window.localStorage.setItem("cortex.onboarding.v2", "complete");
    render(<OnboardingV2Wizard mode="demo" api={makeOkApi()} />);

    // No rehydrate — wizard ignores the flag.
    expect(
      await screen.findByRole("button", { name: /analyze my brand/i }),
    ).toBeInTheDocument();
  });

  it("renders the Demo badge on the rail topbar (step 0)", () => {
    render(<OnboardingV2Wizard mode="demo" api={makeOkApi()} />);
    expect(screen.getByText("Demo")).toBeInTheDocument();
  });

  it("Set up later does NOT write to localStorage in demo mode", () => {
    render(<OnboardingV2Wizard mode="demo" api={makeOkApi()} />);

    fireEvent.click(screen.getByRole("button", { name: /set up later/i }));
    expect(window.localStorage.getItem("cortex.onboarding.v2")).toBeNull();
  });

  it("Enter Discover restarts the wizard and never calls router.push", async () => {
    render(<OnboardingV2Wizard mode="demo" api={makeOkApi()} />);

    fireEvent.click(screen.getByRole("button", { name: /set up later/i }));
    const enterDiscover = await screen.findByRole("button", {
      name: /enter discover/i,
    });
    fireEvent.click(enterDiscover);

    // Restarted: back to step 0 (the Analyze button is visible again).
    expect(
      await screen.findByRole("button", { name: /analyze my brand/i }),
    ).toBeInTheDocument();
    expect(router.push).not.toHaveBeenCalled();
  });
});
