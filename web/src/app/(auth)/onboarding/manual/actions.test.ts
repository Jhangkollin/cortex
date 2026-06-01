import { describe, expect, it, vi } from "vitest";

import type { Session } from "next-auth";

// Hoist mocks so factories can reference them before module evaluation.
// `vi.mock` is hoisted by Vitest's transform, but the factory bodies run at
// module-eval time. Shared mock functions are defined via `vi.hoisted` so
// they exist in the hoisting phase and can be referenced by both `vi.mock`
// factories and test assertions.
const mocks = vi.hoisted(() => ({
  auth: vi.fn(),
  updateBrand: vi.fn(),
  completeOnboarding: vi.fn(),
}));

vi.mock("@/lib/auth", () => ({
  auth: mocks.auth,
}));

vi.mock("@/lib/cortex-api", () => ({
  updateBrand: mocks.updateBrand,
  completeOnboarding: mocks.completeOnboarding,
}));

import { completeBrandOnboarding } from "./actions";

const VALID_SESSION: Session = {
  user: {
    name: "Founder",
    email: "a@b.c",
    cortexUserId: "u1",
    activeContext: {
      kind: "brand",
      id: "b1",
      role: "admin",
      capabilities: ["edit_brand_settings"],
    },
  },
  expires: "2099-01-01T00:00:00.000Z",
};

describe("completeBrandOnboarding", () => {
  it("calls updateBrand then completeOnboarding and returns brandId + brandDisplayName", async () => {
    mocks.auth.mockResolvedValue(VALID_SESSION);
    mocks.updateBrand.mockResolvedValue({
      id: "b1",
      display_name: "Acme",
      industry: null,
      domain: null,
      created_at: "2024-01-01T00:00:00.000Z",
    });
    mocks.completeOnboarding.mockResolvedValue({
      onboarded_at: "2024-01-01T00:00:00.000Z",
    });

    const result = await completeBrandOnboarding({ companyName: "Acme" });

    // updateBrand must be called with correct claims and brandId
    expect(mocks.updateBrand).toHaveBeenCalledWith(
      {
        cortexUserId: "u1",
        email: "a@b.c",
        displayName: "Founder",
        activeContext: VALID_SESSION.user!.activeContext,
      },
      "b1",
      { display_name: "Acme" },
    );

    // completeOnboarding must be called after updateBrand with the same claims shape
    expect(mocks.completeOnboarding).toHaveBeenCalledWith(
      {
        cortexUserId: "u1",
        email: "a@b.c",
        displayName: "Founder",
        activeContext: VALID_SESSION.user!.activeContext,
      },
      "b1",
    );

    // Return shape matches CompleteBrandOnboardingResult
    expect(result).toEqual({ brandId: "b1", brandDisplayName: "Acme" });

    // Order: updateBrand before completeOnboarding
    const updateOrder = mocks.updateBrand.mock.invocationCallOrder[0];
    const completeOrder = mocks.completeOnboarding.mock.invocationCallOrder[0];
    expect(updateOrder).toBeLessThan(completeOrder!);
  });

  it("rejects with descriptive error and does NOT call completeOnboarding when there is no active brand context", async () => {
    mocks.auth.mockResolvedValue({
      ...VALID_SESSION,
      user: {
        ...VALID_SESSION.user,
        activeContext: undefined,
      },
    });
    mocks.updateBrand.mockClear();
    mocks.completeOnboarding.mockClear();

    await expect(
      completeBrandOnboarding({ companyName: "Acme" }),
    ).rejects.toThrow(
      "No active brand context. Pick a workspace from the persona picker first.",
    );

    expect(mocks.completeOnboarding).not.toHaveBeenCalled();
  });
});
