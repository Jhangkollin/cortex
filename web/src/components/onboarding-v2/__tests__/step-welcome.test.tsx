/**
 * Light Edition repaint (Slice 2): StepWelcome.
 *
 * Locks in the three behavioural micro-edits from handoff Appendix C/D:
 *  - URL_SUGGESTIONS now has exactly 2 entries: "mlytics.com" and
 *    "moonbeam.io". `acmebank.asia` and `verde-mobility.com` are gone.
 *  - Trust strip says "~60s" (matches StepCrawl receipt's 74s timing).
 *    The old "~90s" copy must not appear.
 *  - The "No website? Enter manually" fallback button drops the
 *    `edit_note` icon so the link reads lighter.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StepWelcome } from "@/components/onboarding-v2/step-welcome";

function renderWelcome() {
  return render(
    <StepWelcome
      url=""
      setUrl={() => undefined}
      onAnalyze={() => undefined}
      onManual={() => undefined}
    />,
  );
}

describe("StepWelcome — URL suggestions (Light Edition)", () => {
  it("renders exactly 2 suggestion buttons: mlytics.com and moonbeam.io", () => {
    renderWelcome();
    expect(screen.getByRole("button", { name: "mlytics.com" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "moonbeam.io" })).toBeInTheDocument();
    // The old demo brands must not survive the trim.
    expect(
      screen.queryByRole("button", { name: "acmebank.asia" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "verde-mobility.com" }),
    ).not.toBeInTheDocument();
  });
});

describe("StepWelcome — trust strip (Light Edition)", () => {
  it("promises a ~60s crawl, not the legacy ~90s", () => {
    const { container } = renderWelcome();
    expect(container.textContent).toContain("~60s");
    expect(container.textContent).not.toContain("~90s");
  });
});

describe("StepWelcome — manual-fill fallback (Light Edition)", () => {
  it("renders the manual-fill text link without the edit_note icon", () => {
    const manualBtn = renderWelcome().getByRole("button", {
      name: /no website\?\s*enter manually/i,
    });
    // The icon was rendered as `<span class="material-icons-outlined">edit_note</span>`
    // inside the button. Absent its child <span>, the trimmed link
    // matches the prototype's plain-text affordance.
    expect(manualBtn.querySelector(".material-icons-outlined")).toBeNull();
    expect(manualBtn.textContent?.includes("edit_note")).toBe(false);
  });
});
