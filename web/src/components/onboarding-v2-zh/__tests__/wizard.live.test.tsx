/**
 * Regression net for the live-mode zh wizard after the lift from
 * /onboarding/v2/zh-TW/page.tsx into the shared <OnboardingV2WizardZh> component.
 *
 * Uses fireEvent (the existing repo convention — see page-load-states.test.tsx)
 * and a hand-rolled OnboardingApi fake with vi.fn() spies. No global mocking
 * of getOnboardingApi() needed because the wizard now takes the api as a prop.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  CRAWL_TASKS,
  DEPLOY_AGENTS,
  DEPLOY_LOG,
  EXTRACTED_BRAND,
  LIVE_QUESTIONS,
  MEDIA_NETWORK,
  VOICE_TONES,
} from "@/components/onboarding-v2-zh/data";
import { OnboardingV2WizardZh } from "@/components/onboarding-v2-zh/wizard";
import type { OnboardingApi } from "@/lib/onboarding/api";
import { router } from "@tests/helpers/session-mock-state";

// The post-onboarding interstitial (StepPreparingReport, shared with the en
// wizard) the live zh wizard now routes through imports a "use server" actions
// module. Mock it so the wizard renders in jsdom, and keep loadReportState
// pending so the interstitial parks on its "Skip to dashboard" state.
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

describe("OnboardingV2WizardZh — mode='live'", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("renders step 0 (URL entry) on mount", async () => {
    const api = makeOkApi();
    const onComplete = vi.fn(async () => {});
    render(<OnboardingV2WizardZh mode="live" api={api} onComplete={onComplete} />);

    expect(
      await screen.findByRole("button", { name: /分析我的品牌/i }),
    ).toBeInTheDocument();
  });

  it("does not render the Demo badge in live mode", () => {
    const api = makeOkApi();
    const onComplete = vi.fn(async () => {});
    render(<OnboardingV2WizardZh mode="live" api={api} onComplete={onComplete} />);

    expect(screen.queryByText("Demo")).not.toBeInTheDocument();
  });

  it("稍後再設定 writes the completion flag to localStorage", () => {
    const api = makeOkApi();
    const onComplete = vi.fn(async () => {});
    render(<OnboardingV2WizardZh mode="live" api={api} onComplete={onComplete} />);

    fireEvent.click(screen.getByRole("button", { name: /稍後再設定/i }));
    expect(window.localStorage.getItem("cortex.onboarding.v2")).toBe("complete");
  });

  it("進入 Discover (via 稍後再設定 → step 7) calls onComplete once then routes through the report-preparing interstitial", async () => {
    const api = makeOkApi();
    const onComplete = vi.fn(async () => {});
    render(<OnboardingV2WizardZh mode="live" api={api} onComplete={onComplete} />);

    // Skip-to-end shortcut: 稍後再設定 jumps directly to step 7.
    fireEvent.click(screen.getByRole("button", { name: /稍後再設定/i }));
    const enterDiscover = await screen.findByRole("button", {
      name: /進入 Discover/i,
    });
    fireEvent.click(enterDiscover);

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalledTimes(1);
    });

    // Instead of navigating straight to the dashboard, the wizard now shows the
    // LOCALIZED report-preparing interstitial (zh sibling). The final hop to
    // /brand/dashboard is owned by the interstitial's onDone, which has not
    // fired yet. The skip control renders Traditional Chinese copy, proving the
    // zh wizard no longer falls back to the English interstitial.
    expect(
      await screen.findByRole("button", { name: /先進入儀表板/ }),
    ).toBeInTheDocument();
    expect(router.push).not.toHaveBeenCalled();
  });

  it("進入 Discover with a failing onComplete surfaces the error inline and suppresses router.push", async () => {
    const api = makeOkApi();
    const onComplete = vi.fn(async () => {
      throw new Error("server action boom");
    });
    render(<OnboardingV2WizardZh mode="live" api={api} onComplete={onComplete} />);

    fireEvent.click(screen.getByRole("button", { name: /稍後再設定/i }));
    const enterDiscover = await screen.findByRole("button", {
      name: /進入 Discover/i,
    });
    fireEvent.click(enterDiscover);

    expect(await screen.findByRole("alert")).toHaveTextContent(/server action boom/i);
    expect(router.push).not.toHaveBeenCalled();
  });
});
