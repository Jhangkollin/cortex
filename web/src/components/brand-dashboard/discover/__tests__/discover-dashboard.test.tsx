import { describe, test, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { DrawerProvider } from "../drawer-context";
import { DiscoverDashboard } from "../discover-dashboard";

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
    expect(screen.getByText("48")).toBeInTheDocument();
    expect(screen.getByText("相關問題數 (TOP 500 樣樣)")).toBeInTheDocument();
    expect(container.querySelectorAll(".alert")).toHaveLength(3);
    expect(container.querySelectorAll(".fnl-nm")).toHaveLength(5);
    expect(container.querySelector(".grid")).toBeTruthy();
    expect(container.querySelector(".q10")).toBeTruthy();
    expect(container.querySelector(".geo-opp")).toBeTruthy();
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
