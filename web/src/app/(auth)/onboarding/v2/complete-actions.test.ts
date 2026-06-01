import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Session } from "next-auth";

// ---------------------------------------------------------------------------
// Hoist-safe mocks (vi.mock is hoisted; factories run at module scope before
// imports, so refs defined outside vi.hoisted() would be undefined).
// Pattern mirrors analyze-actions.test.ts in this directory.
//
// NOTE: brand_report owns its UI-state in its own table, so the web handoff is
// the single arming path — completeV2Onboarding calls `armReportCelebrate`
// after `completeOnboarding` (the founder holds VIEW_BRAND_DASHBOARD). We
// assert below that the arm IS called and is resilient to failure.
// ---------------------------------------------------------------------------

const { completeOnboardingMock, generateReportMock, armReportCelebrateMock } =
  vi.hoisted(() => ({
    completeOnboardingMock: vi.fn(async (): Promise<void> => {}),
    generateReportMock: vi.fn(async () => ({
      reportId: "BIQ-001",
      status: "pending",
      estimatedSeconds: 120,
      pollUrl: "/v1/brand/b1/report/BIQ-001",
    })),
    armReportCelebrateMock: vi.fn(async (): Promise<void> => {}),
  }));

vi.mock("@/lib/cortex-api", () => ({
  completeOnboarding: completeOnboardingMock,
  generateReport: generateReportMock,
  armReportCelebrate: armReportCelebrateMock,
}));

// ---------------------------------------------------------------------------
// Session fixtures
// ---------------------------------------------------------------------------

const BRAND_SESSION: Session = {
  user: {
    name: "Founder",
    email: "founder@acmebank.asia",
    cortexUserId: "u1",
    activeContext: {
      kind: "brand",
      id: "b1",
      role: "admin",
      capabilities: ["view_brand_dashboard", "edit_brand_settings"],
    },
  },
  expires: "2099-01-01T00:00:00.000Z",
};

// authMock is re-configured per test — must be hoisted for the mock factory.
const { authMock } = vi.hoisted(() => ({
  authMock: vi.fn(async (): Promise<Session> => BRAND_SESSION),
}));

vi.mock("@/lib/auth", () => ({
  auth: authMock,
}));

import { completeV2Onboarding } from "./complete-actions";

describe("completeV2Onboarding", () => {
  beforeEach(() => {
    authMock.mockReset();
    completeOnboardingMock.mockReset();
    generateReportMock.mockReset();
    armReportCelebrateMock.mockReset();
  });

  it("calls completeOnboarding with the correct claims and brandId when session is valid", async () => {
    authMock.mockResolvedValue(BRAND_SESSION);
    completeOnboardingMock.mockResolvedValue(undefined);
    generateReportMock.mockResolvedValue({
      reportId: "BIQ-001",
      status: "pending",
      estimatedSeconds: 120,
      pollUrl: "/v1/brand/b1/report/BIQ-001",
    });

    await completeV2Onboarding();

    expect(completeOnboardingMock).toHaveBeenCalledOnce();
    expect(completeOnboardingMock).toHaveBeenCalledWith(
      {
        cortexUserId: "u1",
        email: "founder@acmebank.asia",
        displayName: "Founder",
        activeContext: BRAND_SESSION.user!.activeContext,
      },
      "b1",
    );
  });

  it("triggers report generation after onboarding completes", async () => {
    authMock.mockResolvedValue(BRAND_SESSION);
    completeOnboardingMock.mockResolvedValue(undefined);
    generateReportMock.mockResolvedValue({
      reportId: "BIQ-001",
      status: "pending",
      estimatedSeconds: 120,
      pollUrl: "/v1/brand/b1/report/BIQ-001",
    });

    await completeV2Onboarding();

    expect(generateReportMock).toHaveBeenCalledOnce();
  });

  it("arms the celebration via armReportCelebrate after onboarding completes", async () => {
    authMock.mockResolvedValue(BRAND_SESSION);
    completeOnboardingMock.mockResolvedValue(undefined);
    generateReportMock.mockResolvedValue({
      reportId: "BIQ-001",
      status: "pending",
      estimatedSeconds: 120,
      pollUrl: "/v1/brand/b1/report/BIQ-001",
    });

    await completeV2Onboarding();

    // brand_report owns its UI state — the web handoff is the single arming
    // path (founder holds VIEW_BRAND_DASHBOARD).
    expect(armReportCelebrateMock).toHaveBeenCalledOnce();
    expect(armReportCelebrateMock).toHaveBeenCalledWith(
      {
        cortexUserId: "u1",
        email: "founder@acmebank.asia",
        displayName: "Founder",
        activeContext: BRAND_SESSION.user!.activeContext,
      },
      "b1",
    );
  });

  it("does not throw if generateReport fails (resilient)", async () => {
    authMock.mockResolvedValue(BRAND_SESSION);
    completeOnboardingMock.mockResolvedValue(undefined);
    generateReportMock.mockRejectedValue(new Error("LLM offline"));

    // Should NOT throw — failures here are non-fatal.
    await expect(completeV2Onboarding()).resolves.toBeUndefined();
  });

  it("does not throw if armReportCelebrate fails (resilient)", async () => {
    authMock.mockResolvedValue(BRAND_SESSION);
    completeOnboardingMock.mockResolvedValue(undefined);
    generateReportMock.mockResolvedValue({
      reportId: "BIQ-001",
      status: "pending",
      estimatedSeconds: 120,
      pollUrl: "/v1/brand/b1/report/BIQ-001",
    });
    armReportCelebrateMock.mockRejectedValue(new Error("arm failed"));

    // Should NOT throw — arming failure must not block entering the dashboard.
    await expect(completeV2Onboarding()).resolves.toBeUndefined();
  });

  it("rejects with a descriptive error and does NOT call completeOnboarding when no brand context", async () => {
    const noContextSession: Session = {
      user: {
        name: "Founder",
        email: "founder@acmebank.asia",
        cortexUserId: "u1",
        // no activeContext
      },
      expires: "2099-01-01T00:00:00.000Z",
    };
    authMock.mockResolvedValue(noContextSession);

    await expect(completeV2Onboarding()).rejects.toThrow(
      "No active brand context. Pick a workspace from the persona picker first.",
    );
    expect(completeOnboardingMock).not.toHaveBeenCalled();
  });
});
