import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { FaqBlock, type FaqItem } from "@/components/marketing/faq-block";

const ITEMS: FaqItem[] = [
  { q: "What's a 'seat' in Cortex?", a: "One human login." },
  { q: "Is there a free tier?", a: "No free production tier." },
  { q: "Annual discount?", a: "20% off list price." },
];

describe("FaqBlock", () => {
  it("renders the section heading 'Questions, before you buy.'", () => {
    render(<FaqBlock items={ITEMS} />);
    expect(
      screen.getByRole("heading", { name: /questions,\s*before you buy/i }),
    ).toBeTruthy();
  });

  it("renders every provided question as a disclosure summary", () => {
    render(<FaqBlock items={ITEMS} />);
    for (const item of ITEMS) {
      expect(screen.getByText(item.q)).toBeTruthy();
    }
  });

  it("renders every provided answer body", () => {
    render(<FaqBlock items={ITEMS} />);
    for (const item of ITEMS) {
      expect(screen.getByText(item.a)).toBeTruthy();
    }
  });

  it("opens the first item by default so the surface does not look closed", () => {
    // Spec §FAQ: 'First card is `open` by default so the surface doesn't look closed.'
    const { container } = render(<FaqBlock items={ITEMS} />);
    const detailsList = container.querySelectorAll("details");
    expect(detailsList.length).toBe(ITEMS.length);
    expect((detailsList[0] as HTMLDetailsElement).open).toBe(true);
    expect((detailsList[1] as HTMLDetailsElement).open).toBe(false);
    expect((detailsList[2] as HTMLDetailsElement).open).toBe(false);
  });

  it("toggles an item open when its summary is clicked (native details behaviour)", () => {
    const { container } = render(<FaqBlock items={ITEMS} />);
    const second = container.querySelectorAll(
      "details",
    )[1] as HTMLDetailsElement;
    expect(second.open).toBe(false);
    // Native <details> toggles via summary click.
    const summary = second.querySelector("summary") as HTMLElement;
    fireEvent.click(summary);
    expect(second.open).toBe(true);
  });
});
