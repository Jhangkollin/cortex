import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("@/lib/auth", () => ({ auth: vi.fn() }));
vi.mock("@/lib/cortex-api", () => ({ listMyBrands: vi.fn() }));

import { auth } from "@/lib/auth";
import { listMyBrands } from "@/lib/cortex-api";

import OnboardingChooser from "../page";

const authMock = vi.mocked(auth);
const listMock = vi.mocked(listMyBrands);

beforeEach(() => vi.clearAllMocks());

async function renderPage() {
  const node = await OnboardingChooser();
  return render(node as React.ReactElement);
}

describe("Onboarding chooser server component", () => {
  it("renders 'Add another brand' when the caller has any onboarded brand", async () => {
    authMock.mockResolvedValue({
      user: {
        email: "okis@m.co",
        cortexUserId: "u-1",
        activeContext: { kind: "brand", id: "brand-1", role: "admin", capabilities: [] },
      },
    } as never);
    listMock.mockResolvedValue([
      { id: "brand-1", display_name: "Hamilton", domain: null, role: "admin", onboarded_at: "2026-05-25T00:00:00Z", created_at: "2026-05-20T00:00:00Z", updated_at: "2026-05-25T00:00:00Z" },
    ] as never);

    await renderPage();
    expect(screen.getByRole("button", { name: /add another brand/i })).toBeInTheDocument();
  });

  it("does NOT render 'Add another brand' for a first-timer (no onboarded brands)", async () => {
    authMock.mockResolvedValue({
      user: {
        email: "okis@m.co",
        cortexUserId: "u-1",
        activeContext: { kind: "brand", id: "brand-1", role: "admin", capabilities: [] },
      },
    } as never);
    listMock.mockResolvedValue([
      { id: "brand-1", display_name: "Okis's brand", domain: null, role: "admin", onboarded_at: null, created_at: "2026-05-26T00:00:00Z", updated_at: "2026-05-26T00:00:00Z" },
    ] as never);

    await renderPage();
    expect(screen.queryByRole("button", { name: /add another brand/i })).not.toBeInTheDocument();
    // The Quick / Manual choices remain
    expect(screen.getByRole("link", { name: /quick.*ai setup/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /manual.*fill a form/i })).toBeInTheDocument();
  });
});
