import { describe, expect, it, vi, beforeEach } from "vitest";

const { redirect, authMock } = vi.hoisted(() => ({
  redirect: vi.fn((url: string) => {
    throw new Error(`REDIRECT:${url}`);
  }),
  authMock: vi.fn(),
}));
vi.mock("next/navigation", () => ({ redirect }));
vi.mock("@/lib/auth", () => ({ auth: authMock }));

import OnboardingLayout from "@/app/(auth)/onboarding/layout";

const children = <div data-testid="child" />;

beforeEach(() => {
  redirect.mockClear();
  authMock.mockReset();
  delete process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH;
});

describe("OnboardingLayout", () => {
  it("redirects to /signin when there is no session", async () => {
    authMock.mockResolvedValue(null);
    await expect(OnboardingLayout({ children })).rejects.toThrow(
      "REDIRECT:/signin",
    );
    expect(redirect).toHaveBeenCalledWith("/signin");
  });

  it("redirects to /signin when the session has no user", async () => {
    authMock.mockResolvedValue({});
    await expect(OnboardingLayout({ children })).rejects.toThrow(
      "REDIRECT:/signin",
    );
    expect(redirect).toHaveBeenCalledWith("/signin");
  });

  it("renders children when an authenticated session is present", async () => {
    authMock.mockResolvedValue({ user: { email: "a@mlytics.com" } });
    const out = await OnboardingLayout({ children });
    expect(out).toBeTruthy();
    expect(redirect).not.toHaveBeenCalled();
  });

  it("renders children without calling auth() when dev bypass is on", async () => {
    process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH = "true";
    const out = await OnboardingLayout({ children });
    expect(out).toBeTruthy();
    expect(authMock).not.toHaveBeenCalled();
    expect(redirect).not.toHaveBeenCalled();
  });
});
