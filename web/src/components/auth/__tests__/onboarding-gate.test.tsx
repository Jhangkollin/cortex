import { describe, expect, it, vi, beforeEach } from "vitest";

const { redirect, authMock, getOnboardingStatus } = vi.hoisted(() => ({
  redirect: vi.fn((url: string) => {
    throw new Error(`REDIRECT:${url}`);
  }),
  authMock: vi.fn(),
  getOnboardingStatus: vi.fn(),
}));
vi.mock("next/navigation", () => ({ redirect }));
vi.mock("@/lib/auth", () => ({ auth: authMock }));
vi.mock("@/lib/cortex-api", () => ({
  getOnboardingStatus,
  OnboardingStatusError: class extends Error {
    constructor(public status: number) {
      super();
    }
  },
}));

import { resolveGateDestination } from "@/components/auth/onboarding-gate";
import { OnboardingStatusError } from "@/lib/cortex-api";

const brandSession = {
  user: {
    email: "a@mlytics.com",
    cortexUserId: "u",
    activeContext: { kind: "brand", id: "b", role: "admin", capabilities: [] },
  },
};

beforeEach(() => {
  redirect.mockClear();
  authMock.mockReset();
  getOnboardingStatus.mockReset();
  delete process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH;
});

describe("resolveGateDestination", () => {
  it("renders through when dev bypass on (no auth call)", async () => {
    process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH = "true";
    expect(await resolveGateDestination()).toBe("render");
    expect(authMock).not.toHaveBeenCalled();
  });
  it("→ /signin when no session", async () => {
    authMock.mockResolvedValue(null);
    expect(await resolveGateDestination()).toBe("/signin");
  });
  it("→ /persona when session but no brand context", async () => {
    authMock.mockResolvedValue({
      user: { email: "a@mlytics.com", cortexUserId: "u" },
    });
    expect(await resolveGateDestination()).toBe("/persona");
  });
  it("→ /onboarding when brand ctx but not onboarded", async () => {
    authMock.mockResolvedValue(brandSession);
    getOnboardingStatus.mockResolvedValue({ onboarded: false });
    expect(await resolveGateDestination()).toBe("/onboarding");
  });
  it("renders when onboarded", async () => {
    authMock.mockResolvedValue(brandSession);
    getOnboardingStatus.mockResolvedValue({ onboarded: true });
    expect(await resolveGateDestination()).toBe("render");
  });
  it("→ /error on 401 status fetch", async () => {
    authMock.mockResolvedValue(brandSession);
    getOnboardingStatus.mockRejectedValue(new OnboardingStatusError(401));
    expect(await resolveGateDestination()).toBe("/error");
  });
  it("→ /error on 403 status fetch", async () => {
    authMock.mockResolvedValue(brandSession);
    getOnboardingStatus.mockRejectedValue(new OnboardingStatusError(403));
    expect(await resolveGateDestination()).toBe("/error");
  });
  it("→ /onboarding on 404 status fetch", async () => {
    authMock.mockResolvedValue(brandSession);
    getOnboardingStatus.mockRejectedValue(new OnboardingStatusError(404));
    expect(await resolveGateDestination()).toBe("/onboarding");
  });
  it("→ retry on 5xx status fetch", async () => {
    authMock.mockResolvedValue(brandSession);
    getOnboardingStatus.mockRejectedValue(new OnboardingStatusError(503));
    expect(await resolveGateDestination()).toBe("retry");
  });
});
