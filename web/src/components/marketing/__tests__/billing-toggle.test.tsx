import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import {
  BillingToggle,
  type BillingPeriod,
} from "@/components/marketing/billing-toggle";

function renderToggle(
  initial: BillingPeriod = "monthly",
  onChange: (next: BillingPeriod) => void = () => {},
) {
  return render(<BillingToggle value={initial} onChange={onChange} />);
}

describe("BillingToggle", () => {
  it("renders both Monthly and Annual options as buttons", () => {
    renderToggle();
    // getByRole throws if missing, so the call is the assertion.
    expect(screen.getByRole("button", { name: /monthly/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /annual/i })).toBeTruthy();
  });

  it("marks the current value as the active option (aria-pressed)", () => {
    renderToggle("monthly");
    expect(
      screen
        .getByRole("button", { name: /monthly/i })
        .getAttribute("aria-pressed"),
    ).toBe("true");
    expect(
      screen
        .getByRole("button", { name: /annual/i })
        .getAttribute("aria-pressed"),
    ).toBe("false");
  });

  it("calls onChange with the new period when the inactive option is clicked", () => {
    const onChange = vi.fn();
    renderToggle("monthly", onChange);
    fireEvent.click(screen.getByRole("button", { name: /annual/i }));
    expect(onChange).toHaveBeenCalledWith("annual");
  });

  it("does not call onChange when the already-active option is clicked", () => {
    // Prevents redundant re-renders of the price grid.
    const onChange = vi.fn();
    renderToggle("monthly", onChange);
    fireEvent.click(screen.getByRole("button", { name: /monthly/i }));
    expect(onChange).not.toHaveBeenCalled();
  });

  it("renders a SAVE 20% pill alongside the Annual label", () => {
    // From handoff §V1: 'SAVE 20%' inline with Annual label · teal-700 on teal-050.
    renderToggle();
    expect(screen.getByText(/save\s*20%/i)).toBeTruthy();
  });
});
