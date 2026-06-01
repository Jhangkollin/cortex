import { afterEach, describe, expect, it, vi } from "vitest";

import {
  completeOnboarding,
  getOnboardingStatus,
  OnboardingStatusError,
} from "@/lib/cortex-api";

const CLAIMS = {
  cortexUserId: "u1",
  email: "a@mlytics.com",
  displayName: "A",
  activeContext: { kind: "brand" as const, id: "b1", role: "admin", capabilities: [] },
};

afterEach(() => vi.unstubAllGlobals());

describe("getOnboardingStatus", () => {
  it("GETs the status endpoint and returns the body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (): Promise<Response> =>
        new Response(JSON.stringify({ onboarded: true }), { status: 200 }),
      ),
    );
    await expect(getOnboardingStatus(CLAIMS as never, "b1")).resolves.toEqual({ onboarded: true });
  });

  it("throws OnboardingStatusError carrying the HTTP status on non-2xx", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (): Promise<Response> => new Response("Forbidden", { status: 403 })),
    );
    await expect(getOnboardingStatus(CLAIMS as never, "b1")).rejects.toBeInstanceOf(
      OnboardingStatusError,
    );
    await expect(getOnboardingStatus(CLAIMS as never, "b1")).rejects.toMatchObject({
      status: 403,
    });
  });
});

describe("completeOnboarding", () => {
  it("POSTs the complete endpoint", async () => {
    const fetchMock = vi.fn(async (): Promise<Response> =>
      new Response(JSON.stringify({ onboarded_at: "2026-05-19T00:00:00Z" }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);
    await completeOnboarding(CLAIMS as never, "b1");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://cortex-api.test/v1/brand/b1/onboarding/complete",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("throws on !ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (): Promise<Response> => new Response("boom", { status: 500 })),
    );
    await expect(completeOnboarding(CLAIMS as never, "b1")).rejects.toThrow();
  });
});
