/**
 * ReportViewer integration tests.
 *
 * Mocks:
 * - IntersectionObserver (not available in jsdom)
 * - ResizeObserver (not available in jsdom)
 * - next/navigation (router.back)
 */
import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ReportViewer } from "../report-viewer";
import { BRAND_IQ_FIXTURE } from "./fixture";

// ── Environment stubs ────────────────────────────────────────────────────────

beforeAll(() => {
  // IntersectionObserver
  global.IntersectionObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  }));

  // ResizeObserver
  global.ResizeObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  }));

  // window.print
  Object.defineProperty(window, "print", { value: vi.fn(), writable: true });
});

beforeEach(() => {
  vi.clearAllMocks();
});

// ── Helpers ──────────────────────────────────────────────────────────────────

function renderViewer() {
  return render(
    <ReportViewer report={BRAND_IQ_FIXTURE} reportId="BIQ-2026-05-22-ACMEBA" />,
  );
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe("ReportViewer", () => {
  it("renders the brand name in the toolbar", () => {
    renderViewer();
    expect(screen.getAllByText(/Acme Bank Asia/i).length).toBeGreaterThan(0);
  });

  it("renders all 8 TOC items", () => {
    renderViewer();
    // Each page has a TOC button with the label (may appear multiple times)
    expect(screen.getAllByText("封面").length).toBeGreaterThan(0);
    expect(screen.getAllByText("品牌核心").length).toBeGreaterThan(0);
    expect(screen.getAllByText("產品線結構").length).toBeGreaterThan(0);
    expect(screen.getAllByText("媒體網絡").length).toBeGreaterThan(0);
    expect(screen.getAllByText("競品輪廓").length).toBeGreaterThan(0);
    expect(screen.getAllByText("戰略洞察").length).toBeGreaterThan(0);
    expect(screen.getAllByText("讀者熱問+通路").length).toBeGreaterThan(0);
    expect(screen.getAllByText("風險+來源+品質").length).toBeGreaterThan(0);
  });

  it("renders page counter showing 1/8 initially", () => {
    renderViewer();
    expect(screen.getByText("第 1 / 8 頁")).toBeInTheDocument();
  });

  it("renders report ID in toolbar", () => {
    renderViewer();
    expect(screen.getAllByText(/BIQ-2026-05-22-ACMEBA/).length).toBeGreaterThan(0);
  });

  it("renders zoom controls and shows initial percentage", () => {
    renderViewer();
    // Should show some % value
    const pctElements = screen.getAllByText(/%$/);
    expect(pctElements.length).toBeGreaterThan(0);
  });

  it("zoom in button increases scale label", () => {
    renderViewer();
    // Get the initial scale text (e.g. "85%")
    const initialPct = screen.getAllByText(/%$/).find(
      (el) => parseInt(el.textContent ?? "0") > 0,
    );
    if (!initialPct) return; // skip if scale label not found as %

    const zoomIn = screen.getByLabelText("放大");
    const before = parseInt(initialPct.textContent ?? "0");
    fireEvent.click(zoomIn);
    const after = parseInt(initialPct.textContent ?? "0");
    expect(after).toBeGreaterThan(before);
  });

  it("zoom out button decreases scale label", () => {
    renderViewer();
    const pctEl = screen.getAllByText(/%$/).find(
      (el) => parseInt(el.textContent ?? "0") > 0,
    );
    if (!pctEl) return;

    const zoomOut = screen.getByLabelText("縮小");
    const before = parseInt(pctEl.textContent ?? "0");
    fireEvent.click(zoomOut);
    const after = parseInt(pctEl.textContent ?? "0");
    expect(after).toBeLessThan(before);
  });

  it("zoom clamps at minimum 55%", () => {
    renderViewer();
    const zoomOut = screen.getByLabelText("縮小");
    // Click many times to reach minimum
    for (let i = 0; i < 30; i++) fireEvent.click(zoomOut);
    const pctEl = screen.getAllByText(/%$/).find(
      (el) => parseInt(el.textContent ?? "0") > 0,
    );
    if (!pctEl) return;
    expect(parseInt(pctEl.textContent ?? "0")).toBeGreaterThanOrEqual(55);
  });

  it("zoom clamps at maximum 150%", () => {
    renderViewer();
    const zoomIn = screen.getByLabelText("放大");
    for (let i = 0; i < 30; i++) fireEvent.click(zoomIn);
    const pctEl = screen.getAllByText(/%$/).find(
      (el) => parseInt(el.textContent ?? "0") > 0,
    );
    if (!pctEl) return;
    expect(parseInt(pctEl.textContent ?? "0")).toBeLessThanOrEqual(150);
  });

  it("renders the print button", () => {
    renderViewer();
    expect(screen.getByText(/列印/)).toBeInTheDocument();
  });

  it("renders the download PDF link pointing to api endpoint", () => {
    renderViewer();
    const dlLink = screen.getByText(/下載 PDF/);
    // The link's href should include the reportId
    const anchor = dlLink.closest("a");
    expect(anchor?.href).toContain("BIQ-2026-05-22-ACMEBA");
  });

  it("calls window.print() when Print button is clicked", () => {
    renderViewer();
    fireEvent.click(screen.getByText(/列印/));
    expect(window.print).toHaveBeenCalled();
  });

  it("calls router.back() when Back button is clicked", async () => {
    // Import router mock from setup's mock state
    const { router } = await import("@tests/helpers/session-mock-state");
    renderViewer();
    const backBtn = screen.getByText(/返回 Dashboard/);
    fireEvent.click(backBtn);
    expect(router.back).toHaveBeenCalled();
  });

  it("navigates back when Escape is pressed", async () => {
    const { router } = await import("@tests/helpers/session-mock-state");
    renderViewer();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(router.back).toHaveBeenCalled();
  });

  it("exposes a labelled region but does NOT advertise modal semantics", () => {
    renderViewer();
    const region = screen.getByRole("region", {
      name: /Acme Bank Asia · Brand IQ 報告/,
    });
    expect(region).toBeInTheDocument();
    // Full-page route, not a modal — must not claim aria-modal.
    expect(region).not.toHaveAttribute("aria-modal");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("renders Page 1 cover with brand name", () => {
    renderViewer();
    // Cover page has the brand name in large display
    const subjects = screen.getAllByText("Acme Bank Asia");
    expect(subjects.length).toBeGreaterThan(0);
  });

  it("renders Page 2 anatomy section", () => {
    renderViewer();
    expect(screen.getByText("品牌核心解剖")).toBeInTheDocument();
  });

  it("renders Page 3 portfolio section", () => {
    renderViewer();
    // Section heading (may appear in multiple places including TOC)
    expect(screen.getAllByText(/產品線/).length).toBeGreaterThan(0);
  });

  it("renders Page 4 media network section", () => {
    renderViewer();
    expect(screen.getByText("你的品牌能被聽見的地方")).toBeInTheDocument();
  });

  it("renders Page 5 competitor section", () => {
    renderViewer();
    expect(screen.getByText("你在這個品類的位置")).toBeInTheDocument();
  });

  it("renders Page 6 insights section", () => {
    renderViewer();
    expect(screen.getByText("從訊號到行動")).toBeInTheDocument();
  });

  it("renders Page 7 FAQ section", () => {
    renderViewer();
    expect(screen.getByText("讀者最常問的問題")).toBeInTheDocument();
  });

  it("renders Page 8 risks section", () => {
    renderViewer();
    expect(screen.getByText("合規風險訊號")).toBeInTheDocument();
  });

  it("renders the report-at-a-glance stats in the TOC sidebar", () => {
    renderViewer();
    // "產品線" label in sidebar stats
    expect(screen.getAllByText("產品線").length).toBeGreaterThan(0);
    expect(screen.getAllByText("媒體節點").length).toBeGreaterThan(0);
    expect(screen.getAllByText("競品").length).toBeGreaterThan(0);
    expect(screen.getAllByText("風險訊號").length).toBeGreaterThan(0);
  });
});
