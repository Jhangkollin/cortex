/**
 * BrandReportCelebration tests (COR-82).
 *
 * Tests:
 *   - Modal renders with role="dialog" + aria-modal
 *   - Esc key calls onClose
 *   - Primary CTA (查看 Brand IQ 報告) calls onClose
 *   - Close button calls onClose
 *   - Primary link href routes to /brand/reports/{reportId}
 *   - Subject name from report.report.meta.subject is rendered
 *   - Focus moves to the close button on mount
 *   - Tab / Shift-Tab focus trap wraps within the dialog (a11y, item 3)
 */

import { describe, it, test, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { BrandReportCelebration } from "../brand-report-celebration";
import type { ReportEnvelope } from "@/app/brand/dashboard/report-types";

vi.mock("@/app/brand/dashboard/report-actions", () => ({}));

function _readyReport(): ReportEnvelope {
  return {
    reportId: "BIQ-cel-001",
    status: "ready",
    error: null,
    // Partial fixture — only the `meta` fields the modal reads. Cast through
    // `unknown` because the test intentionally omits the other 14 required
    // BrandIqReport fields the celebration never touches.
    report: {
      meta: {
        subject: "CelebCo",
        monogram: "C",
        primaryMarket: "TW",
        extendedMarkets: [],
        reportDate: "2026-05-24",
        pageCount: 12,
        reportId: "BIQ-cel-001",
      },
    } as unknown as ReportEnvelope["report"],
  };
}

describe("BrandReportCelebration", () => {
  test("renders as a dialog with aria-modal", () => {
    render(
      <BrandReportCelebration
        report={_readyReport()}
        onClose={() => {}}
      />,
    );
    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeInTheDocument();
    expect(dialog).toHaveAttribute("aria-modal", "true");
  });

  test("renders subject from report meta", () => {
    render(
      <BrandReportCelebration
        report={_readyReport()}
        onClose={() => {}}
      />,
    );
    expect(screen.getByText("CelebCo")).toBeInTheDocument();
  });

  test("close button calls onClose", () => {
    const onClose = vi.fn();
    render(
      <BrandReportCelebration
        report={_readyReport()}
        onClose={onClose}
      />,
    );
    fireEvent.click(screen.getByLabelText("關閉"));
    expect(onClose).toHaveBeenCalledOnce();
  });

  test("primary CTA (查看 Brand IQ 報告) calls onClose", () => {
    const onClose = vi.fn();
    render(
      <BrandReportCelebration
        report={_readyReport()}
        onClose={onClose}
      />,
    );
    fireEvent.click(screen.getByText(/查看 Brand IQ 報告/));
    expect(onClose).toHaveBeenCalledOnce();
  });

  test("Esc key calls onClose", () => {
    const onClose = vi.fn();
    render(
      <BrandReportCelebration
        report={_readyReport()}
        onClose={onClose}
      />,
    );
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledOnce();
  });

  test("primary CTA link points to /brand/reports/{reportId}", () => {
    render(
      <BrandReportCelebration
        report={_readyReport()}
        onClose={() => {}}
      />,
    );
    const link = screen.getByText(/查看 Brand IQ 報告/).closest("a");
    expect(link?.href).toContain("/brand/reports/BIQ-cel-001");
  });

  test("focuses the close button on mount", () => {
    render(
      <BrandReportCelebration
        report={_readyReport()}
        onClose={() => {}}
      />,
    );
    expect(document.activeElement).toBe(screen.getByLabelText("關閉"));
  });

  test("Tab from the last focusable element wraps back to the first (focus trap)", () => {
    const { container } = render(
      <BrandReportCelebration
        report={_readyReport()}
        onClose={() => {}}
      />,
    );
    const focusable = container.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])',
    );
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    // Park focus on the last element, then Tab — the trap wraps to the first.
    last.focus();
    expect(document.activeElement).toBe(last);
    fireEvent.keyDown(document, { key: "Tab" });
    expect(document.activeElement).toBe(first);
  });

  test("Shift-Tab from the first focusable element wraps to the last (focus trap)", () => {
    const { container } = render(
      <BrandReportCelebration
        report={_readyReport()}
        onClose={() => {}}
      />,
    );
    const focusable = container.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])',
    );
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    first.focus();
    expect(document.activeElement).toBe(first);
    fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(last);
  });

  // ─── Light Edition structure assertions (2026-05-27) ─────────────────────

  describe("Light Edition layout", () => {
    function fixture() {
      return {
        reportId: "BIQ-TEST-1",
        status: "ready" as const,
        report: {
          meta: {
            subject: "Acme Bank Asia",
            monogram: "A",
            pageCount: 8,
          },
          productLines: [{}, {}, {}, {}, {}, {}, {}],          // 7
          mediaNetwork: [{}, {}, {}, {}, {}, {}],               // 6
          competitors: [{}, {}, {}],                            // 3
          risks: [{}, {}, {}, {}],                              // 4
        } as never,
      };
    }

    it("renders the Cortex · Brand Agent · Live top-bar caption", () => {
      render(<BrandReportCelebration report={fixture()} onClose={() => {}} />);
      expect(screen.getByText(/Cortex · Brand Agent · Live/i)).toBeInTheDocument();
    });

    it("renders the gold achievement pill (成就解鎖)", () => {
      render(<BrandReportCelebration report={fixture()} onClose={() => {}} />);
      expect(screen.getByText(/成就解鎖.*Brand IQ/)).toBeInTheDocument();
    });

    it("renders the 4-stat mini grid with live counts from the envelope", () => {
      render(<BrandReportCelebration report={fixture()} onClose={() => {}} />);
      expect(screen.getByText("產品線")).toBeInTheDocument();
      expect(screen.getByText("媒體節點")).toBeInTheDocument();
      expect(screen.getByText("競品")).toBeInTheDocument();
      expect(screen.getByText("風險訊號")).toBeInTheDocument();
      expect(screen.getByText("7")).toBeInTheDocument();   // productLines
      expect(screen.getByText("6")).toBeInTheDocument();   // mediaNetwork
      expect(screen.getByText("3")).toBeInTheDocument();   // competitors
      expect(screen.getByText("4")).toBeInTheDocument();   // risks
    });

    it("primary CTA links to the report viewer route", () => {
      render(<BrandReportCelebration report={fixture()} onClose={() => {}} />);
      const primary = screen.getByRole("link", { name: /查看 Brand IQ 報告/ });
      expect(primary.getAttribute("href")).toMatch(/\/brand\/reports\/BIQ-TEST-1/);
    });

    it("falls back to '0' in stat cells when envelope sections are missing", () => {
      const f = fixture();
      // Override with meta-only shape (no productLines etc.) to test ?? 0 fallback.
      f.report = { meta: { subject: "Acme Bank Asia", monogram: "A", pageCount: 8 } } as never;
      render(<BrandReportCelebration report={f} onClose={() => {}} />);
      expect(screen.getAllByText("0").length).toBeGreaterThanOrEqual(4);
    });
  });
});
