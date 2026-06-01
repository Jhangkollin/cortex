import { describe, test, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { PriorityAlerts } from "../priority-alerts";
import { Topbar } from "../topbar";
import { BASE_DATA } from "@/lib/discover/mock";

describe("PriorityAlerts", () => {
  test("renders 3 intent-coded alert cards", () => {
    const { container } = render(
      <PriorityAlerts alerts={BASE_DATA.alerts} />,
    );
    expect(container.querySelectorAll(".alert")).toHaveLength(3);
    expect(container.querySelector(".alert.is-warn")).toBeTruthy();
    expect(container.querySelector(".alert.is-opp")).toBeTruthy();
    expect(container.querySelector(".alert.is-sig")).toBeTruthy();
    expect(screen.getByText("GAP")).toBeInTheDocument();
  });
});

describe("Topbar", () => {
  test("renders crumb, title, subtitle and filter chips", () => {
    const { container } = render(<Topbar />);
    expect(screen.getByText("BRAND CORTEX")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Discover" }),
    ).toBeInTheDocument();
    expect(container.querySelector(".top")).toBeTruthy();
    expect(screen.getByText("All markets")).toBeInTheDocument();
    expect(screen.getByText("Last 30 days")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Export/i })).toBeInTheDocument();
  });
});
