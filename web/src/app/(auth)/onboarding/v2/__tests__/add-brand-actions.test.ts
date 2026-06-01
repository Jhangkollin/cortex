import { describe, expect, it, vi, beforeEach } from "vitest";

// Same trap as the other onboarding action tests: this is a "use server" file
// importing @/lib/auth (next-auth). Mock both before importing the module
// under test.
vi.mock("@/lib/auth", () => ({ auth: vi.fn() }));
vi.mock("@/lib/cortex-api", () => ({ createBrand: vi.fn() }));

import { auth } from "@/lib/auth";
import { createBrand } from "@/lib/cortex-api";

import { createAnotherBrandAction } from "../add-brand-actions";

const authMock = vi.mocked(auth);
const createBrandMock = vi.mocked(createBrand);

beforeEach(() => {
  vi.clearAllMocks();
});

describe("createAnotherBrandAction", () => {
  it("creates a new brand and returns the new activeContext", async () => {
    authMock.mockResolvedValue({
      user: {
        email: "okis@m.co",
        cortexUserId: "user-uuid-1",
        name: "Okis",
        activeContext: { kind: "brand", id: "old-brand", role: "admin", capabilities: [] },
      },
    } as never);
    createBrandMock.mockResolvedValue({
      brand: { id: "new-brand-uuid", display_name: "Okis Chuang's brand", industry: null, domain: null, created_at: "" },
      role: "admin",
      capabilities: ["view_brand_dashboard", "edit_brand_settings"],
    } as never);

    const out = await createAnotherBrandAction();

    expect(createBrandMock).toHaveBeenCalledTimes(1);
    expect(out.brandId).toBe("new-brand-uuid");
    expect(out.activeContext).toEqual({
      kind: "brand",
      id: "new-brand-uuid",
      role: "admin",
      capabilities: ["view_brand_dashboard", "edit_brand_settings"],
    });
  });

  it("throws when there is no session", async () => {
    authMock.mockResolvedValue(null as never);
    await expect(createAnotherBrandAction()).rejects.toThrow(/not signed in/i);
    expect(createBrandMock).not.toHaveBeenCalled();
  });

  it("throws when cortexUserId is missing", async () => {
    authMock.mockResolvedValue({
      user: { email: "okis@m.co", activeContext: { kind: "brand", id: "old" } },
    } as never);
    await expect(createAnotherBrandAction()).rejects.toThrow(/sign-in did not complete/i);
    expect(createBrandMock).not.toHaveBeenCalled();
  });
});
