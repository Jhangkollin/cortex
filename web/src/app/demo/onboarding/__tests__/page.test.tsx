/**
 * Smoke test for the en demo route. Verifies:
 *   - the server page exports a metadata.title for the browser tab,
 *   - the client wrapper renders <OnboardingV2Wizard> with mode="demo" and
 *     a MockOnboardingApi instance (NOT the live HTTP-or-mock factory output).
 *
 * Mocks the wizard so the test exercises only the wiring, not the wizard
 * body (which has its own dedicated tests in components/onboarding-v2/__tests__).
 */
import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { MockOnboardingApi } from "@/lib/onboarding/mock-api";

const wizardSpy = vi.fn();
vi.mock("@/components/onboarding-v2/wizard", () => ({
  OnboardingV2Wizard: (props: unknown) => {
    wizardSpy(props);
    return null;
  },
}));

import { DemoOnboardingClient } from "@/app/demo/onboarding/client";
import DemoOnboardingPage, { metadata } from "@/app/demo/onboarding/page";

describe("/demo/onboarding (en)", () => {
  it("server page exports metadata with the demo tab title", () => {
    expect(metadata.title).toBe("Cortex · Demo");
  });

  it("server page renders the client wrapper", () => {
    const { container } = render(<DemoOnboardingPage />);
    expect(container).toBeTruthy();
  });

  it("client wrapper renders OnboardingV2Wizard with mode='demo' and a MockOnboardingApi instance", () => {
    wizardSpy.mockClear();
    render(<DemoOnboardingClient />);

    expect(wizardSpy).toHaveBeenCalledTimes(1);
    const props = wizardSpy.mock.calls[0][0] as {
      mode: string;
      api: unknown;
      onComplete?: unknown;
    };
    expect(props.mode).toBe("demo");
    expect(props.api).toBeInstanceOf(MockOnboardingApi);
    expect(props.onComplete).toBeUndefined();
  });
});
