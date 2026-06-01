import { describe, test, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

// Control the session shape per test.
const mockUseMockSession = vi.fn();
vi.mock("@/components/auth/mock-session-provider", () => ({
  useMockSession: () => mockUseMockSession(),
}));

// Stub the three children to sentinels so we assert *which* render, not their
// internals (they have their own tests).
vi.mock("@/components/brand-dashboard/brand-report-surface", () => ({
  BrandReportSurface: () => <div data-testid="report-surface" />,
}));
vi.mock("@/components/brand-dashboard/discover/discover-dashboard", () => ({
  DiscoverDashboard: () => <div data-testid="discover-dashboard" />,
}));
vi.mock("@/components/brand-dashboard/empty-discover", () => ({
  EmptyDiscover: () => <div data-testid="empty-discover" />,
}));

import BrandDashboardPage from "../page";

describe("BrandDashboardPage", () => {
  beforeEach(() => {
    mockUseMockSession.mockReset();
  });

  // The regression this hotfix guards: a freshly-onboarded brand has 0 connected
  // sources (→ EmptyDiscover) but DOES have a first report. The report surface
  // must render in the empty state, not only the populated one.
  test("renders the report surface AND the empty stage for a fresh brand (0 sources)", () => {
    mockUseMockSession.mockReturnValue({
      session: { demo: false, connectedSourceCount: 0 },
    });
    render(<BrandDashboardPage />);
    expect(screen.getByTestId("report-surface")).toBeInTheDocument();
    expect(screen.getByTestId("empty-discover")).toBeInTheDocument();
    expect(screen.queryByTestId("discover-dashboard")).toBeNull();
  });

  test("renders the report surface AND the populated stage when sources are connected", () => {
    mockUseMockSession.mockReturnValue({
      session: { demo: false, connectedSourceCount: 3 },
    });
    render(<BrandDashboardPage />);
    expect(screen.getByTestId("report-surface")).toBeInTheDocument();
    expect(screen.getByTestId("discover-dashboard")).toBeInTheDocument();
    expect(screen.queryByTestId("empty-discover")).toBeNull();
  });

  test("renders the report surface AND the populated stage in demo mode (0 sources)", () => {
    mockUseMockSession.mockReturnValue({
      session: { demo: true, connectedSourceCount: 0 },
    });
    render(<BrandDashboardPage />);
    expect(screen.getByTestId("report-surface")).toBeInTheDocument();
    expect(screen.getByTestId("discover-dashboard")).toBeInTheDocument();
    expect(screen.queryByTestId("empty-discover")).toBeNull();
  });
});
