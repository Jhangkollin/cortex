import { describe, test, expect, vi, beforeEach } from "vitest";

// Mock auth + the cortex-api fetchers so we can drive the claims path without
// pulling in next-auth (which imports next/server and breaks under jsdom).
const authMock = vi.fn();
vi.mock("@/lib/auth", () => ({ auth: () => authMock() }));

const getReportUiState = vi.fn();
const listBrandReports = vi.fn();
const fetchBrandReport = vi.fn();
vi.mock("@/lib/cortex-api", () => ({
  getReportUiState: (...a: unknown[]) => getReportUiState(...a),
  listBrandReports: (...a: unknown[]) => listBrandReports(...a),
  fetchBrandReport: (...a: unknown[]) => fetchBrandReport(...a),
  consumeReportCelebrate: vi.fn(),
  dismissReportHero: vi.fn(),
  generateReport: vi.fn(),
}));

import { loadReportState } from "../report-actions";

const BRAND = "019e42c0-5d03-74ab-ac84-23920e1451ee";

describe("report-actions / loadReportState claims tolerance", () => {
  beforeEach(() => {
    authMock.mockReset();
    getReportUiState.mockReset();
    listBrandReports.mockReset();
    fetchBrandReport.mockReset();
    getReportUiState.mockResolvedValue({
      celebratePending: true,
      heroDismissed: false,
    });
    listBrandReports.mockResolvedValue([
      { reportId: "BIQ-1", version: "v1", createdAt: "2026-05-24", status: "ready", current: true },
    ]);
    fetchBrandReport.mockResolvedValue({
      reportId: "BIQ-1",
      status: "ready",
      error: null,
      report: {},
    });
  });

  // Regression: a brand session with NO cortexUserId (the UAT case) must still
  // load report state. Previously _claims() bailed on a missing cortexUserId and
  // returned defaults, so the hero/celebration never showed even with a ready,
  // celebrate-pending report. The KB tolerates the same gap (cortexUserId ?? "").
  test("loads report state when the session has a brand context but no cortexUserId", async () => {
    authMock.mockResolvedValue({
      user: { activeContext: { kind: "brand", id: BRAND }, email: "x@y.z" },
    });

    const rs = await loadReportState();

    // It must NOT bail — the api calls fire with an empty-string cortexUserId.
    expect(getReportUiState).toHaveBeenCalledWith(
      expect.objectContaining({
        cortexUserId: "",
        activeContext: { kind: "brand", id: BRAND },
      }),
      BRAND,
    );
    expect(listBrandReports).toHaveBeenCalled();
    expect(rs.uiState.celebratePending).toBe(true);
    expect(rs.latestReport?.status).toBe("ready");
  });

  test("returns defaults and makes no api calls when there is no brand context", async () => {
    authMock.mockResolvedValue({ user: { activeContext: null } });

    const rs = await loadReportState();

    expect(getReportUiState).not.toHaveBeenCalled();
    expect(listBrandReports).not.toHaveBeenCalled();
    expect(rs.uiState.celebratePending).toBe(false);
    expect(rs.latestReport).toBeNull();
  });
});
