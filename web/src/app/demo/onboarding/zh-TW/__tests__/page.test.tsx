/**
 * Smoke test for the zh demo route. Verifies:
 *   - the server page exports a metadata.title for the browser tab,
 *   - the client wrapper renders <OnboardingV2WizardZh> with mode="demo" and
 *     a MockOnboardingApiZh instance (the zh-aware mock adapter — not the
 *     en MockOnboardingApi, which would serve English data into a zh UI).
 *
 * Mocks the wizard so the test exercises only the wiring, not the wizard
 * body (which has its own dedicated tests in components/onboarding-v2-zh/__tests__).
 */
import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { MockOnboardingApiZh } from "@/lib/onboarding/mock-api-zh";

const wizardSpy = vi.fn();
vi.mock("@/components/onboarding-v2-zh/wizard", () => ({
  OnboardingV2WizardZh: (props: unknown) => {
    wizardSpy(props);
    return null;
  },
}));

import { DemoOnboardingZhClient } from "@/app/demo/onboarding/zh-TW/client";
import DemoOnboardingZhPage, { metadata } from "@/app/demo/onboarding/zh-TW/page";

describe("/demo/onboarding/zh-TW (zh)", () => {
  it("server page exports metadata with the demo tab title", () => {
    expect(metadata.title).toBe("Cortex · 體驗版");
  });

  it("server page renders the client wrapper", () => {
    const { container } = render(<DemoOnboardingZhPage />);
    expect(container).toBeTruthy();
  });

  it("client wrapper renders OnboardingV2WizardZh with mode='demo' and a MockOnboardingApiZh instance", () => {
    wizardSpy.mockClear();
    render(<DemoOnboardingZhClient />);

    expect(wizardSpy).toHaveBeenCalledTimes(1);
    const props = wizardSpy.mock.calls[0][0] as {
      mode: string;
      api: unknown;
      onComplete?: unknown;
    };
    expect(props.mode).toBe("demo");
    expect(props.api).toBeInstanceOf(MockOnboardingApiZh);
    expect(props.onComplete).toBeUndefined();
  });
});
