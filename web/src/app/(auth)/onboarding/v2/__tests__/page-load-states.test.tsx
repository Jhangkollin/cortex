/**
 * Regression suite for the onboarding-v2 load/error UX.
 *
 * Originally written for PR #29 review Issues 1 & 2. The SP-3a
 * scanning-UX fix deliberately *evolved* that contract — this file now
 * locks in the NEW contract, and documents why, so the change is a
 * conscious decision and not silent drift.
 *
 * Issue 1 (intent preserved): the wizard must never render a blank
 * document, must show an explicit state while work is in flight, and must
 * surface an error + retry when the *real* risky call fails. The risky
 * call is no longer the mount load — it is the user-triggered brand
 * analyze (HttpOnboardingApi → Server Action → cortex-api, ~25s). Mount
 * now loads only the modeled scaffolding (local constants); a modeled
 * failure is intentionally non-fatal (the wizard chrome still renders).
 *
 * Issue 2 (intent preserved, behavior evolved): mount and restart must
 * not diverge and must funnel through a single shared path. NEW contract
 * (product decision, 2026-05-18): neither mount nor restart auto-runs the
 * real analyze. Mount renders step 0 (URL entry) immediately; restart
 * returns to step 0. Analyze runs only when the user clicks "Analyze my
 * brand", via the single shared `runAnalyze`. This kills the prior
 * mount-time blank-spinner + a wasted real LLM extraction of the
 * hardcoded INITIAL_URL — the exact regression the UX fix removed.
 *
 * Strategy: replace the `getOnboardingApi` factory with a controllable
 * fake whose promises we resolve/reject by hand. Assertions target
 * observable UI (URL-entry screen, error copy + retry control, recovery).
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
} from "@/components/onboarding-v2/data";
import type { OnboardingApi } from "@/lib/onboarding/api";

// Controllable seam fake. `mode` flips between resolve and reject so a
// single instance can model "first attempt fails, retry succeeds".
let mode: "ok" | "fail" = "ok";
const analyzeSpy = vi.fn<(url: string) => void>();

function makeApi(): OnboardingApi {
  const guard = <T,>(v: T): Promise<T> =>
    mode === "ok" ? Promise.resolve(v) : Promise.reject(new Error("boom"));
  return {
    analyzeBrand: (url: string) => {
      analyzeSpy(url);
      return guard(EXTRACTED_BRAND);
    },
    // Modeled scaffolding always resolves — these are local constants in
    // production too; their failure is non-fatal by design.
    getCrawlTasks: () => Promise.resolve(CRAWL_TASKS),
    getMediaNetwork: () => Promise.resolve(MEDIA_NETWORK),
    getLiveQuestions: () => Promise.resolve(LIVE_QUESTIONS),
    getVoiceTones: () => Promise.resolve(VOICE_TONES),
    getDeployAgents: () => Promise.resolve(DEPLOY_AGENTS),
    getDeployLog: () => Promise.resolve(DEPLOY_LOG),
  };
}

vi.mock("@/app/(auth)/onboarding/v2/analyze-actions", () => ({
  startAnalyzeAction: vi.fn(),
  pollAnalyzeAction: vi.fn(),
}));

// complete-actions is a "use server" file that imports next-auth's server-side
// helpers (next/server). Stub it out here so the page can be rendered in jsdom
// without pulling in server-only modules.
vi.mock("@/app/(auth)/onboarding/v2/complete-actions", () => ({
  completeV2Onboarding: vi.fn(async () => {}),
}));

// media-actions (SP-MEDIA) is likewise a "use server" file importing
// next-auth's server-side helpers. The vi.mock of "@/lib/onboarding/api"
// below does `importActual`, which pulls the real http-api → media-actions
// chain; stub it so jsdom doesn't try to resolve next/server. Mirrors the
// convention in http-api.test.ts / get-onboarding-api.test.ts.
vi.mock("@/app/(auth)/onboarding/v2/media-actions", () => ({
  startMediaNetworkAction: vi.fn(),
  pollMediaNetworkAction: vi.fn(),
}));

// brand-voice-actions and weekly-questions-actions are also "use server" files
// importing @/lib/auth → next-auth. The `@/lib/onboarding/api` importActual
// below pulls in http-api, which imports all four action files; stub the two
// missing ones so jsdom never tries to resolve `next/server` (Next.js 16
// dropped `package.json#exports`, breaking Node's ESM resolution).
vi.mock("@/app/(auth)/onboarding/v2/brand-voice-actions", () => ({
  startBrandVoiceAction: vi.fn(),
  pollBrandVoiceAction: vi.fn(),
}));
vi.mock("@/app/(auth)/onboarding/v2/weekly-questions-actions", () => ({
  startWeeklyQuestionsAction: vi.fn(),
  pollWeeklyQuestionsAction: vi.fn(),
}));

// report-actions is a "use server" file (next-auth → next/server). The wizard
// now transitively imports the post-onboarding interstitial that uses it; stub
// it so the page renders in jsdom without pulling server-only modules.
vi.mock("@/app/brand/dashboard/report-actions", () => ({
  consumeCelebrate: vi.fn().mockResolvedValue(undefined),
  loadReportState: vi.fn(() => new Promise(() => {})),
}));

// add-brand-actions is a "use server" file that imports next-auth server helpers
// (next-auth/lib/env.js → next/server). The wizard now transitively imports it;
// stub it so the page renders in jsdom without pulling server-only modules.
vi.mock("@/app/(auth)/onboarding/v2/add-brand-actions", () => ({
  listMyBrandsAction: vi.fn(async () => []),
  createAnotherBrandAction: vi.fn(async () => ({
    brandId: "test-brand-id",
    activeContext: { kind: "brand", id: "test-brand-id", role: "admin", capabilities: [] },
  })),
}));

vi.mock("@/lib/onboarding/api", async () => {
  const actual =
    await vi.importActual<typeof import("@/lib/onboarding/api")>(
      "@/lib/onboarding/api",
    );
  return { ...actual, getOnboardingApi: () => makeApi() };
});

// Imported AFTER the mock is registered.
import OnboardingV2Page from "@/app/(auth)/onboarding/v2/page";

beforeEach(() => {
  mode = "ok";
  analyzeSpy.mockClear();
});

afterEach(() => {
  vi.restoreAllMocks();
});

function clickAnalyze() {
  // StepWelcome only fires onAnalyze for a valid URL; set a known-good one.
  const input = screen.getByRole("textbox");
  fireEvent.change(input, { target: { value: "https://example.com" } });
  fireEvent.click(screen.getByRole("button", { name: /analyze my brand/i }));
}

describe("OnboardingV2Page — load UX (Issue 1, evolved)", () => {
  it("never renders a blank document", () => {
    const { container } = render(<OnboardingV2Page />);
    expect(container.firstChild).not.toBeNull();
  });

  it("renders step 0 (URL entry) immediately — no analyze on mount", async () => {
    render(<OnboardingV2Page />);
    expect(
      await screen.findByRole("button", { name: /analyze my brand/i }),
    ).toBeInTheDocument();
    // The real LLM analyze must NOT run until the user asks for it.
    expect(analyzeSpy).not.toHaveBeenCalled();
  });

  it("surfaces an error + retry when the user-triggered analyze fails, then recovers", async () => {
    mode = "fail";
    render(<OnboardingV2Page />);
    await screen.findByRole("button", { name: /analyze my brand/i });

    clickAnalyze();

    const retry = await screen.findByRole("button", {
      name: /retry|try again/i,
    });
    expect(retry).toBeInTheDocument();
    expect(analyzeSpy).toHaveBeenCalled();

    // Recover: retry now succeeds → error state clears.
    mode = "ok";
    fireEvent.click(retry);
    await waitFor(() => {
      expect(
        screen.queryByRole("button", { name: /retry|try again/i }),
      ).not.toBeInTheDocument();
    });
  });
});

describe("OnboardingV2Page — mount/restart cannot diverge (Issue 2, evolved)", () => {
  it("neither mount nor restart auto-runs analyze; restart returns to URL entry", async () => {
    render(<OnboardingV2Page />);
    await screen.findByRole("button", { name: /analyze my brand/i });

    // Contract: no analyze until an explicit user request.
    expect(analyzeSpy).not.toHaveBeenCalled();

    // On step 0 the TopBar's onExit (the mlytics logo lockup button —
    // Light Edition renamed from "Welcome to Cortex", now showing the real
    // brand PNG hooked via `data-mly-mark="lockup"`) is wired to restart().
    // We locate the button via the lockup image's closest <button> to
    // disambiguate from the "mlytics.com" sample-URL chip on step 0 (which
    // also has "mlytics" in its accessible name).
    const lockupImg = document.querySelector('img[data-mly-mark="lockup"]');
    expect(lockupImg).not.toBeNull();
    const lockupButton = lockupImg!.closest("button");
    expect(lockupButton).not.toBeNull();
    fireEvent.click(lockupButton!);

    // Restart lands back on URL entry and still triggers no analyze —
    // mount and restart share the same single (no-auto-analyze) path.
    expect(
      await screen.findByRole("button", { name: /analyze my brand/i }),
    ).toBeInTheDocument();
    expect(analyzeSpy).not.toHaveBeenCalled();
  });
});
