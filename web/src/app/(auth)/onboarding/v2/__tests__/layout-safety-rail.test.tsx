import { describe, expect, it, vi, beforeEach } from "vitest";

vi.mock("next/navigation", () => ({ redirect: vi.fn() }));
vi.mock("@/lib/auth", () => ({ auth: vi.fn() }));
vi.mock("@/lib/cortex-api", () => ({ getOnboardingStatus: vi.fn() }));

import { redirect } from "next/navigation";
import { auth } from "@/lib/auth";
import { getOnboardingStatus } from "@/lib/cortex-api";

import OnboardingV2Layout from "../layout";

const redirectMock = vi.mocked(redirect);
const authMock = vi.mocked(auth);
const statusMock = vi.mocked(getOnboardingStatus);

beforeEach(() => vi.clearAllMocks());

describe("OnboardingV2Layout (safety rail)", () => {
  it("redirects to /onboarding when active brand is already onboarded", async () => {
    authMock.mockResolvedValue({
      user: {
        email: "okis@m.co",
        cortexUserId: "u-1",
        activeContext: { kind: "brand", id: "brand-1", role: "admin", capabilities: [] },
      },
    } as never);
    statusMock.mockResolvedValue({ onboarded: true } as never);

    await OnboardingV2Layout({ children: <div /> } as never);

    expect(redirectMock).toHaveBeenCalledWith("/onboarding");
  });

  it("renders children when active brand is not onboarded", async () => {
    authMock.mockResolvedValue({
      user: {
        email: "okis@m.co",
        cortexUserId: "u-1",
        activeContext: { kind: "brand", id: "brand-1", role: "admin", capabilities: [] },
      },
    } as never);
    statusMock.mockResolvedValue({ onboarded: false } as never);

    const out = await OnboardingV2Layout({ children: <div data-testid="kids" /> } as never);
    expect(redirectMock).not.toHaveBeenCalled();
    expect(out).toBeTruthy();
  });

  it("redirects when active context is missing or not a brand", async () => {
    authMock.mockResolvedValue({ user: { email: "okis@m.co", cortexUserId: "u-1" } } as never);
    await OnboardingV2Layout({ children: <div /> } as never);
    expect(redirectMock).toHaveBeenCalledWith("/onboarding");
  });
});
