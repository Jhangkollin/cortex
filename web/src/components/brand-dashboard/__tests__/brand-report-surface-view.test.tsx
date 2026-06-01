import { describe, test, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { BrandReportSurfaceView } from "../brand-report-surface-view";
import {
  READY_FIXTURE,
  PREVIEW_UI_STATE,
} from "../report-surface-fixture";

// Pure presentational component — no server actions, no data fetching. We feed
// it the fixture + flags directly and assert on the rendered hero/celebration.

function renderView(
  overrides: Partial<React.ComponentProps<typeof BrandReportSurfaceView>> = {},
) {
  return render(
    <BrandReportSurfaceView
      showHero={false}
      showCelebration={false}
      report={READY_FIXTURE}
      heroDismissed={PREVIEW_UI_STATE.heroDismissed}
      onDismissHero={vi.fn()}
      onRetry={vi.fn()}
      onCloseCelebration={vi.fn()}
      {...overrides}
    />,
  );
}

describe("BrandReportSurfaceView", () => {
  test("renders the celebration when showCelebration is true with READY_FIXTURE", () => {
    renderView({ showCelebration: true });
    // The celebration is a role="dialog" overlay labelled by the brand subject.
    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeInTheDocument();
    expect(screen.getByText("Acme Bank Asia")).toBeInTheDocument();
  });

  test("renders nothing when both flags are false", () => {
    const { container } = renderView();
    expect(container).toBeEmptyDOMElement();
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  test("renders the hero when showHero is true with READY_FIXTURE", () => {
    renderView({ showHero: true });
    // Ready hero copy: "<subject> 的品牌側寫已準備好".
    expect(screen.getByText("的品牌側寫已準備好", { exact: false })).toBeInTheDocument();
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  test("invokes onCloseCelebration when Escape is pressed while the celebration is shown", () => {
    const onCloseCelebration = vi.fn();
    renderView({ showCelebration: true, onCloseCelebration });
    // The celebration registers a document-level keydown handler that calls
    // onClose on Escape (see discover/brand-report-celebration.tsx).
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onCloseCelebration).toHaveBeenCalledTimes(1);
  });
});
