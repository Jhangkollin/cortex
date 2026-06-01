import {
  describe,
  test,
  expect,
  vi,
  beforeEach,
  afterEach,
} from "vitest";
import { render, screen, act } from "@testing-library/react";

import { BrandReportSurface } from "../brand-report-surface";
import * as reportActions from "@/app/brand/dashboard/report-actions";
import type { ReportState } from "@/app/brand/dashboard/report-types";

// Mock the server actions — BrandReportSurface calls loadReportState on mount,
// retryReport from the hero retry CTA, and consume/dismiss on interaction.
vi.mock("@/app/brand/dashboard/report-actions", () => ({
  loadReportState: vi.fn(),
  retryReport: vi.fn(),
  consumeCelebrate: vi.fn().mockResolvedValue(undefined),
  dismissHero: vi.fn().mockResolvedValue(undefined),
}));

const loadReportState = vi.mocked(reportActions.loadReportState);
const retryReport = vi.mocked(reportActions.retryReport);

const NO_REPORT: ReportState = {
  uiState: { celebratePending: false, heroDismissed: false, celebrateReady: false },
  latestReport: null,
  brandId: "00000000-0000-0000-0000-000000000001",
};

function readyReport(): ReportState {
  return {
    uiState: { celebratePending: true, heroDismissed: false, celebrateReady: true },
    // Partial fixture — only the meta fields the components read. Cast through
    // `unknown` (the full BrandIqReport has 14 more required fields).
    latestReport: {
      reportId: "BIQ-1",
      status: "ready",
      error: null,
      report: {
        meta: {
          subject: "PollCo",
          monogram: "P",
          primaryMarket: "TW",
          extendedMarkets: [],
          reportDate: "2026-05-24",
          pageCount: 8,
          reportId: "BIQ-1",
        },
      },
    } as unknown as ReportState["latestReport"],
    brandId: "00000000-0000-0000-0000-000000000001",
  };
}

function generatingReport(): ReportState {
  return {
    uiState: { celebratePending: true, heroDismissed: false, celebrateReady: false },
    latestReport: {
      reportId: "BIQ-1",
      status: "running",
      error: null,
      report: null,
    },
    brandId: "00000000-0000-0000-0000-000000000001",
  };
}

/**
 * A report whose content is ready (status: "ready") but whose server gate flag
 * `celebrateReady` is false (e.g. already consumed). The celebration must NOT
 * show — proving the gate is the server flag, not the client report status.
 */
function readyReportNotCelebrate(): ReportState {
  const rs = readyReport();
  return {
    ...rs,
    uiState: { celebratePending: true, heroDismissed: false, celebrateReady: false },
  };
}

const ui = async () => {
  let result!: ReturnType<typeof render>;
  await act(async () => {
    result = render(<BrandReportSurface />);
  });
  return result;
};

describe("brand-report-surface", () => {
  beforeEach(() => {
    loadReportState.mockReset();
    retryReport.mockReset();
    loadReportState.mockResolvedValue(NO_REPORT);
  });

  test("renders nothing when there is no report", async () => {
    const { container } = await ui();
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.queryByText("的品牌側寫已準備好")).toBeNull();
    expect(container).toBeEmptyDOMElement();
  });

  test("shows the celebration when a ready report is loaded with celebrateReady", async () => {
    loadReportState.mockResolvedValue(readyReport());
    await ui();
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("PollCo")).toBeInTheDocument();
  });

  test("does NOT show the celebration when the report is ready but celebrateReady is false", async () => {
    // Report content is fully "ready" but the server gate flag is false (e.g.
    // already consumed). The gate is the server flag, not the report status.
    loadReportState.mockResolvedValue(readyReportNotCelebrate());
    await ui();
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  test("shows the celebration purely on celebrateReady when the report is ready", async () => {
    loadReportState.mockResolvedValue(readyReport());
    await ui();
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  test("preview shows the celebration from the fixture without loading state", async () => {
    // No loadReportState mock setup beyond the beforeEach NO_REPORT — preview
    // must NOT depend on the server action at all.
    await act(async () => {
      render(<BrandReportSurface preview />);
    });
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    expect(loadReportState).not.toHaveBeenCalled();
  });
});

describe("brand-report-surface polling", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    loadReportState.mockReset();
    retryReport.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  test("polls while generating + celebratePending, then shows celebration on ready", async () => {
    // First load: still generating. Subsequent polls: ready.
    loadReportState
      .mockResolvedValueOnce(generatingReport())
      .mockResolvedValue(readyReport());

    await act(async () => {
      render(<BrandReportSurface />);
    });

    // Initial load resolved to generating → no celebration yet.
    expect(screen.queryByRole("dialog")).toBeNull();

    // Advance one poll interval; the poll resolves to ready and the
    // act() flush applies the resulting state synchronously.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(4_000);
    });

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    // loadReportState was called again by the poll (>1 total).
    expect(loadReportState.mock.calls.length).toBeGreaterThan(1);
  });

  test("does not poll once the report is terminal (ready) on first load", async () => {
    loadReportState.mockResolvedValue(readyReport());

    await act(async () => {
      render(<BrandReportSurface />);
    });

    const callsAfterMount = loadReportState.mock.calls.length;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(12_000);
    });
    // No additional polls — report was already ready.
    expect(loadReportState.mock.calls.length).toBe(callsAfterMount);
  });
});
