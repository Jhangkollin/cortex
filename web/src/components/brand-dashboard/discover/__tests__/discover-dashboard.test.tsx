import { describe, test, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { DrawerProvider } from "../drawer-context";
import { DiscoverDashboard } from "../discover-dashboard";

// DiscoverDashboard is now purely the populated discover stage (BASE_DATA).
// The Brand IQ report hero + celebration moved to <BrandReportSurface/> —
// see brand-report-surface.test.tsx for that behavior.
function renderStage() {
  return render(
    <DrawerProvider>
      <DiscoverDashboard />
    </DrawerProvider>,
  );
}

describe("discover-dashboard", () => {
  test("renders the canonical BASE_DATA stage", () => {
    const { container } = renderStage();
    expect(screen.getByText("18.4")).toBeInTheDocument();
    expect(screen.getByText("Brand-cited answers")).toBeInTheDocument();
    expect(container.querySelectorAll(".alert")).toHaveLength(3);
    expect(container.querySelectorAll(".blk")).toHaveLength(5);
    expect(container.querySelector(".grid")).toBeTruthy();
  });

  test("does not render the v2.0 Cortex query strip", () => {
    const { container } = renderStage();
    expect(container.querySelector(".cq")).toBeNull();
    expect(screen.queryByText("Show me mortgage topics")).toBeNull();
    expect(
      screen.queryByPlaceholderText(
        "Ask Cortex — your dashboard will answer in place",
      ),
    ).toBeNull();
  });
});
