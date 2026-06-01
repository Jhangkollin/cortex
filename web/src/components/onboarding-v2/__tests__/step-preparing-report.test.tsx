import {
  describe,
  test,
  expect,
  vi,
  beforeEach,
  afterEach,
} from "vitest";
import { render, screen, act, fireEvent } from "@testing-library/react";

import { StepPreparingReport } from "../step-preparing-report";
import { READY_FIXTURE } from "@/components/brand-dashboard/report-surface-fixture";
import * as reportActions from "@/app/brand/dashboard/report-actions";
import type { ReportState } from "@/app/brand/dashboard/report-types";

// The server consume action is "use server" (server-only imports), so we mock
// the module — the interstitial AWAITS consumeCelebrate on celebration close
// before calling onDone (so the dashboard's own load runs after the celebrate
// flag is cleared).
vi.mock("@/app/brand/dashboard/report-actions", () => ({
  consumeCelebrate: vi.fn().mockResolvedValue(undefined),
  // loadReportState is the default for the injectable `loadState` prop. Tests
  // always inject their own, but the mock keeps the import resolvable.
  loadReportState: vi.fn(),
}));

const consumeCelebrate = vi.mocked(reportActions.consumeCelebrate);

const NOT_READY: ReportState = {
  uiState: { celebratePending: true, heroDismissed: false, celebrateReady: false },
  latestReport: null,
  brandId: "b1",
};

const READY: ReportState = {
  uiState: { celebratePending: true, heroDismissed: false, celebrateReady: true },
  latestReport: READY_FIXTURE,
  brandId: "b1",
};

describe("step-preparing-report", () => {
  beforeEach(() => {
    consumeCelebrate.mockReset();
    consumeCelebrate.mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  test("renders the preparing progress state and a Skip control", async () => {
    const loadState = vi.fn().mockResolvedValue(NOT_READY);
    await act(async () => {
      render(<StepPreparingReport onDone={vi.fn()} loadState={loadState} />);
    });

    expect(
      screen.getByText(/preparing your first report/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /skip to dashboard/i }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  test("shows the celebration dialog when a ready state is loaded", async () => {
    const loadState = vi.fn().mockResolvedValue(READY);
    await act(async () => {
      render(<StepPreparingReport onDone={vi.fn()} loadState={loadState} />);
    });

    expect(await screen.findByRole("dialog")).toBeInTheDocument();
  });

  test("closing the celebration awaits consumeCelebrate before calling onDone", async () => {
    // Defer consume so we can observe ordering: onDone must NOT fire until the
    // consume round-trip resolves (otherwise the dashboard re-loads while the
    // server still reports celebrateReady → celebration re-shows).
    let resolveConsume!: () => void;
    consumeCelebrate.mockReturnValue(
      new Promise<void>((resolve) => {
        resolveConsume = resolve;
      }),
    );

    const onDone = vi.fn();
    const loadState = vi.fn().mockResolvedValue(READY);
    await act(async () => {
      render(<StepPreparingReport onDone={onDone} loadState={loadState} />);
    });

    // Close the celebration via the dialog's close button.
    const dialog = await screen.findByRole("dialog");
    await act(async () => {
      fireEvent.click(
        screen.getByRole("button", { name: /關閉/i }),
      );
    });
    expect(dialog).toBeInTheDocument();

    // Consume kicked off, but it hasn't resolved → onDone must still be pending.
    expect(consumeCelebrate).toHaveBeenCalledTimes(1);
    expect(onDone).not.toHaveBeenCalled();

    // Resolve the consume → now (and only now) onDone fires.
    await act(async () => {
      resolveConsume();
    });
    expect(onDone).toHaveBeenCalledTimes(1);
  });

  test("celebration close still navigates when consume fails (finally)", async () => {
    consumeCelebrate.mockRejectedValue(new Error("consume boom"));

    const onDone = vi.fn();
    const loadState = vi.fn().mockResolvedValue(READY);
    await act(async () => {
      render(<StepPreparingReport onDone={onDone} loadState={loadState} />);
    });

    await screen.findByRole("dialog");
    await act(async () => {
      fireEvent.click(
        screen.getByRole("button", { name: /關閉/i }),
      );
    });

    expect(onDone).toHaveBeenCalledTimes(1);
  });

  test("clicking Skip to dashboard calls onDone", async () => {
    const onDone = vi.fn();
    const loadState = vi.fn().mockResolvedValue(NOT_READY);
    await act(async () => {
      render(<StepPreparingReport onDone={onDone} loadState={loadState} />);
    });

    fireEvent.click(
      screen.getByRole("button", { name: /skip to dashboard/i }),
    );
    expect(onDone).toHaveBeenCalledTimes(1);
  });

  test("Skip stops polling so onDone fires exactly once (timeout cannot re-call)", async () => {
    vi.useFakeTimers();
    const onDone = vi.fn();
    const loadState = vi.fn().mockResolvedValue(NOT_READY);

    await act(async () => {
      render(
        <StepPreparingReport
          onDone={onDone}
          loadState={loadState}
          pollMs={1_000}
          timeoutMs={3_000}
        />,
      );
    });

    fireEvent.click(
      screen.getByRole("button", { name: /skip to dashboard/i }),
    );
    expect(onDone).toHaveBeenCalledTimes(1);

    // The interval + timeout must have been cleared on skip — advancing past
    // the timeout must NOT call onDone a second time.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3_000);
    });
    expect(onDone).toHaveBeenCalledTimes(1);
  });

  test("calls onDone after timeout when never ready", async () => {
    vi.useFakeTimers();
    const onDone = vi.fn();
    const loadState = vi.fn().mockResolvedValue(NOT_READY);

    await act(async () => {
      render(
        <StepPreparingReport
          onDone={onDone}
          loadState={loadState}
          pollMs={1_000}
          timeoutMs={3_000}
        />,
      );
    });

    expect(onDone).not.toHaveBeenCalled();

    // Advance past the timeout, flushing polls + the timeout fallback.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3_000);
    });

    expect(onDone).toHaveBeenCalledTimes(1);
  });
});
