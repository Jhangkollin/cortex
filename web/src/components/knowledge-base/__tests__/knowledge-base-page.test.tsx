/**
 * KnowledgeBasePage component tests — COR-83
 *
 * Covers:
 * - Version list renders (featured card + history table)
 * - Preview / Download hrefs point to correct routes
 * - "現行" badge on current version
 * - Other-resources rows show pending state, not invented counts
 * - Empty-state renders when no reports
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { KnowledgeBasePage } from "../knowledge-base-page";
import { FeaturedReportCard } from "../featured-report-card";
import { VersionHistoryTable } from "../version-history-table";
import { OtherResources } from "../other-resources";
import { isCurrent } from "../is-current";
import {
  CURRENT_VERSION,
  ARCHIVED_VERSION,
  VERSIONS_FIXTURE,
} from "./fixture";

// ── isCurrent (SSOT) ──────────────────────────────────────────────────────────

describe("isCurrent", () => {
  it("returns true only for the version with current === true", () => {
    expect(isCurrent(CURRENT_VERSION)).toBe(true);
    expect(isCurrent(ARCHIVED_VERSION)).toBe(false);
  });

  it("ignores status — a non-current 'ready' report is not current", () => {
    // status is generating|ready|failed, never "current"; only the boolean wins.
    expect(isCurrent({ ...ARCHIVED_VERSION, status: "ready" })).toBe(false);
    expect(isCurrent({ ...CURRENT_VERSION, status: "ready" })).toBe(true);
  });
});

// ── Helpers ──────────────────────────────────────────────────────────────────

function renderPage(versions = VERSIONS_FIXTURE) {
  return render(<KnowledgeBasePage versions={versions} />);
}

// ── KnowledgeBasePage ─────────────────────────────────────────────────────────

describe("KnowledgeBasePage", () => {
  beforeEach(() => {
    // no extra setup needed
  });

  it("renders the page title", () => {
    renderPage();
    expect(screen.getByRole("heading", { name: /Knowledge Base/i })).toBeInTheDocument();
  });

  it("renders the breadcrumb", () => {
    renderPage();
    expect(screen.getByText(/BRAND CORTEX/i)).toBeInTheDocument();
  });

  it("renders the active 'Brand Reports' section header", () => {
    renderPage();
    expect(screen.getByTestId("kb-section-header")).toBeInTheDocument();
    expect(screen.getByText("Brand Reports")).toBeInTheDocument();
  });

  it("does NOT expose misleading tab ARIA (no tablist / tab roles)", () => {
    renderPage();
    // These section labels are non-interactive placeholders, not real tabs —
    // they must not advertise tablist/tab semantics.
    expect(screen.queryByRole("tablist")).not.toBeInTheDocument();
    expect(screen.queryAllByRole("tab")).toHaveLength(0);
  });

  it("renders the not-yet-available categories as '準備中' placeholders", () => {
    renderPage();
    // Four dimmed coming-soon labels live in the section header.
    const header = screen.getByTestId("kb-section-header");
    for (const label of ["所有檔案", "產品知識卡", "Brand Voice 樣本", "競品筆記"]) {
      expect(header).toHaveTextContent(label);
    }
  });

  it("renders the featured report card when current version exists", () => {
    renderPage();
    expect(screen.getByTestId("featured-report-card")).toBeInTheDocument();
  });

  it("renders the version history table", () => {
    renderPage();
    expect(screen.getByTestId("version-history-table")).toBeInTheDocument();
  });

  it("renders the other resources section", () => {
    renderPage();
    expect(screen.getByTestId("other-resources")).toBeInTheDocument();
  });

  it("renders the info panel", () => {
    renderPage();
    expect(screen.getByText(/Brand IQ 報告是 onboarding 抓取資料的快照/)).toBeInTheDocument();
  });

  it("shows empty state when no versions", () => {
    renderPage([]);
    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
    expect(screen.getByText(/尚無 Brand IQ 報告/)).toBeInTheDocument();
  });

  it("does NOT show featured card when no versions", () => {
    renderPage([]);
    expect(screen.queryByTestId("featured-report-card")).not.toBeInTheDocument();
  });
});

// ── FeaturedReportCard ────────────────────────────────────────────────────────

describe("FeaturedReportCard", () => {
  function renderCard() {
    return render(<FeaturedReportCard version={CURRENT_VERSION} />);
  }

  it("renders the card", () => {
    renderCard();
    expect(screen.getByTestId("featured-report-card")).toBeInTheDocument();
  });

  it("renders version tag", () => {
    renderCard();
    expect(screen.getByText(CURRENT_VERSION.version)).toBeInTheDocument();
  });

  it("shows 最新 badge for current version", () => {
    renderCard();
    expect(screen.getByText("最新")).toBeInTheDocument();
  });

  it("preview link points to report viewer route", () => {
    renderCard();
    const link = screen.getByTestId("preview-link");
    expect(link).toHaveAttribute("href", `/brand/reports/${CURRENT_VERSION.reportId}`);
  });

  it("download link points to PDF proxy route", () => {
    renderCard();
    const link = screen.getByTestId("download-link");
    expect(link).toHaveAttribute("href", `/brand/reports/${CURRENT_VERSION.reportId}/pdf`);
  });

  it("does NOT show 最新 badge for non-current version", () => {
    render(<FeaturedReportCard version={ARCHIVED_VERSION} />);
    expect(screen.queryByText("最新")).not.toBeInTheDocument();
  });
});

// ── VersionHistoryTable ───────────────────────────────────────────────────────

describe("VersionHistoryTable", () => {
  function renderTable(versions = VERSIONS_FIXTURE) {
    return render(<VersionHistoryTable versions={versions} />);
  }

  it("renders all version rows", () => {
    renderTable();
    expect(screen.getByTestId(`version-row-${CURRENT_VERSION.reportId}`)).toBeInTheDocument();
    expect(screen.getByTestId(`version-row-${ARCHIVED_VERSION.reportId}`)).toBeInTheDocument();
  });

  it("shows 現行 badge for current version", () => {
    renderTable();
    expect(screen.getByTestId(`status-current-${CURRENT_VERSION.reportId}`)).toBeInTheDocument();
    expect(screen.getByText("現行")).toBeInTheDocument();
  });

  it("shows archived badge for non-current version", () => {
    renderTable();
    expect(screen.getByTestId(`status-archived-${ARCHIVED_VERSION.reportId}`)).toBeInTheDocument();
  });

  it("download link for current version points to pdf route", () => {
    renderTable();
    const link = screen.getByTestId(`download-version-${CURRENT_VERSION.reportId}`);
    expect(link).toHaveAttribute("href", `/brand/reports/${CURRENT_VERSION.reportId}/pdf`);
  });

  it("download link for archived version points to pdf route", () => {
    renderTable();
    const link = screen.getByTestId(`download-version-${ARCHIVED_VERSION.reportId}`);
    expect(link).toHaveAttribute("href", `/brand/reports/${ARCHIVED_VERSION.reportId}/pdf`);
  });

  it("renders newest-first (current before archived)", () => {
    renderTable();
    const rows = screen.getAllByTestId(/^version-row-/);
    // Current version (2026-05-22) should appear before archived (2026-05-19)
    const currentIdx = rows.findIndex((r) =>
      r.getAttribute("data-testid")?.includes(CURRENT_VERSION.reportId),
    );
    const archivedIdx = rows.findIndex((r) =>
      r.getAttribute("data-testid")?.includes(ARCHIVED_VERSION.reportId),
    );
    expect(currentIdx).toBeLessThan(archivedIdx);
  });

  it("sorts newest-first even when given oldest-first input", () => {
    // Pass the versions in reverse (oldest-first) order to actually exercise
    // the table's internal sort — the default fixture is already sorted.
    renderTable([ARCHIVED_VERSION, CURRENT_VERSION]);
    const rows = screen.getAllByTestId(/^version-row-/);
    const currentIdx = rows.findIndex((r) =>
      r.getAttribute("data-testid")?.includes(CURRENT_VERSION.reportId),
    );
    const archivedIdx = rows.findIndex((r) =>
      r.getAttribute("data-testid")?.includes(ARCHIVED_VERSION.reportId),
    );
    expect(currentIdx).toBeLessThan(archivedIdx);
  });
});

// ── OtherResources ────────────────────────────────────────────────────────────

describe("OtherResources", () => {
  it("renders all four resource rows", () => {
    render(<OtherResources />);
    expect(screen.getByTestId("resource-product-cards")).toBeInTheDocument();
    expect(screen.getByTestId("resource-brand-voice")).toBeInTheDocument();
    expect(screen.getByTestId("resource-competitor-notes")).toBeInTheDocument();
    expect(screen.getByTestId("resource-weekly-report")).toBeInTheDocument();
  });

  it("marks all rows as pending (準備中)", () => {
    render(<OtherResources />);
    const pendingBadges = screen.getAllByText("準備中");
    expect(pendingBadges.length).toBe(4);
  });

  it("does NOT show any invented count numbers", () => {
    render(<OtherResources />);
    // Prototype had "6 張 / 4 句" — must not appear
    expect(screen.queryByText(/6 張/)).not.toBeInTheDocument();
    expect(screen.queryByText(/4 句/)).not.toBeInTheDocument();
    // Also must not show any "N 張" pattern (digit + 張)
    const allText = document.body.textContent ?? "";
    expect(allText).not.toMatch(/\d+ 張/);
    expect(allText).not.toMatch(/\d+ 句/);
  });

  it("shows pending badge for product cards", () => {
    render(<OtherResources />);
    expect(screen.getByTestId("resource-product-cards-pending")).toBeInTheDocument();
  });

  it("shows pending badge for brand voice", () => {
    render(<OtherResources />);
    expect(screen.getByTestId("resource-brand-voice-pending")).toBeInTheDocument();
  });

  it("shows pending badge for competitor notes", () => {
    render(<OtherResources />);
    expect(screen.getByTestId("resource-competitor-notes-pending")).toBeInTheDocument();
  });

  it("shows pending badge for weekly report", () => {
    render(<OtherResources />);
    expect(screen.getByTestId("resource-weekly-report-pending")).toBeInTheDocument();
  });
});
