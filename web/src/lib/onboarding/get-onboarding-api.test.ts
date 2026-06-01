import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/app/(auth)/onboarding/v2/analyze-actions", () => ({
  startAnalyzeAction: vi.fn(),
  pollAnalyzeAction: vi.fn(),
}));

vi.mock("@/app/(auth)/onboarding/v2/media-actions", () => ({
  startMediaNetworkAction: vi.fn(),
  pollMediaNetworkAction: vi.fn(),
}));

vi.mock("@/app/(auth)/onboarding/v2/weekly-questions-actions", () => ({
  startWeeklyQuestionsAction: vi.fn(),
  pollWeeklyQuestionsAction: vi.fn(),
}));

// brand-voice-actions is a "use server" file importing @/lib/auth → next-auth,
// whose `lib/env.js` imports bare `next/server`. Next.js 16 ships no
// `package.json#exports`, so Node's ESM resolver can't find it and the
// transitive load (api.ts → http-api.ts → brand-voice-actions) blows up
// the test suite. Stub it the same way the other "use server" siblings are.
vi.mock("@/app/(auth)/onboarding/v2/brand-voice-actions", () => ({
  startBrandVoiceAction: vi.fn(),
  pollBrandVoiceAction: vi.fn(),
}));

import { getOnboardingApi } from "./api";
import { HttpOnboardingApi } from "./http-api";
import { MockOnboardingApi } from "./mock-api";

afterEach(() => vi.unstubAllEnvs());

describe("getOnboardingApi", () => {
  it("returns HttpOnboardingApi when the flag is set", () => {
    vi.stubEnv("NEXT_PUBLIC_CORTEX_ONBOARDING_HTTP", "1");
    expect(getOnboardingApi()).toBeInstanceOf(HttpOnboardingApi);
  });
  it("defaults to MockOnboardingApi", () => {
    vi.stubEnv("NEXT_PUBLIC_CORTEX_ONBOARDING_HTTP", "");
    expect(getOnboardingApi()).toBeInstanceOf(MockOnboardingApi);
  });
});
