/**
 * Light Edition repaint (Slice 2): primitives — TopBar logo lockup and
 * StepRail palette. zh-Hant mirror of
 * ../../onboarding-v2/__tests__/primitives.test.tsx — kept in lockstep so a
 * drift on either side surfaces in CI rather than at handoff time.
 *
 * What we lock in here (identical contract to the en tree):
 *  - TopBar renders the real mlytics logo PNG (`data-mly-mark="lockup"`
 *    hook on a next/image <img>, alt="mlytics"). The previous inline-SVG
 *    "M" placeholder + "mlytics · cortex" wordmark span were removed when
 *    the brand handoff shipped the real PNG (chore/real-mlytics-logo).
 *  - StepRail uses the Light Edition palette: active step disc backed by
 *    `--brand-teal`, completed step backed by `--gold`, future step
 *    outlined with `--paper-border`. Asserting on inline style strings is
 *    deliberate — these are token-name contracts the handoff cares about.
 */

import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StepRail, TopBar } from "@/components/onboarding-v2-zh/primitives";
import type { RailIndex } from "@/components/onboarding-v2-zh/data";

const STEPS = [
  "Connect site",
  "Confirm brand",
  "Media network",
  "Weekly questions",
  "Launch Agent",
  "Done",
] as const;

describe("onboarding-v2-zh primitives — TopBar (Light Edition)", () => {
  it("renders the real mlytics logo PNG with the data-mly-mark hook", () => {
    const { container } = render(
      <TopBar
        railStep={0 as RailIndex}
        steps={STEPS}
        onSkip={() => undefined}
        onExit={() => undefined}
      />,
    );

    // The brand mark is now a next/image PNG hooked with
    // `data-mly-mark="lockup"`. Tests find it by data attribute, not by
    // src — next/image rewrites the URL through its loader so the rendered
    // src is not the literal /brand/mlytics-logo.png path.
    const mark = container.querySelector('img[data-mly-mark="lockup"]');
    expect(mark).not.toBeNull();
    expect(mark?.getAttribute("alt")).toBe("mlytics");
  });
});

describe("onboarding-v2-zh primitives — StepRail (Light Edition)", () => {
  // Render at step 2 so we get one completed step (0), one active (2),
  // and three future steps (3-5) in one snapshot.
  function renderRail(step: RailIndex) {
    return render(<StepRail step={step} steps={STEPS} />);
  }

  it("uses --brand-teal for the active step disc", () => {
    const { container } = renderRail(2 as RailIndex);
    // The discs are the innermost spans with width:24px. Pull all of
    // them and assert by index — same approach the handoff uses to
    // verify the rail visually.
    const discs = Array.from(
      container.querySelectorAll<HTMLElement>('span[style*="width: 24px"]'),
    );
    expect(discs).toHaveLength(STEPS.length);
    expect(discs[2].getAttribute("style")).toContain("--brand-teal");
  });

  it("uses --gold for completed step discs", () => {
    const { container } = renderRail(2 as RailIndex);
    const discs = Array.from(
      container.querySelectorAll<HTMLElement>('span[style*="width: 24px"]'),
    );
    // Steps 0 and 1 are completed when active is 2.
    expect(discs[0].getAttribute("style")).toContain("--gold");
    expect(discs[1].getAttribute("style")).toContain("--gold");
  });

  it("uses --paper-border for future step discs", () => {
    const { container } = renderRail(2 as RailIndex);
    const discs = Array.from(
      container.querySelectorAll<HTMLElement>('span[style*="width: 24px"]'),
    );
    // Steps 3-5 are future. They must carry a transparent background
    // and a paper-border outline, not a teal/gold fill.
    [3, 4, 5].forEach((i) => {
      const styleStr = discs[i].getAttribute("style") ?? "";
      expect(styleStr).toContain("--paper-border");
      expect(styleStr).not.toContain("--brand-teal");
      expect(styleStr).not.toContain("--gold");
    });
  });
});
