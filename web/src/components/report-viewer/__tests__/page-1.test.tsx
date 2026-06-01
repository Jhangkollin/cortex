/**
 * Page1 (Cover) unit tests.
 * Validates: brand name renders; the strategic pull-quote uses
 * report.coreJudgement (not hardcoded copy) and is omitted when empty.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Page1 } from "../pages/page-1";
import { BRAND_IQ_FIXTURE } from "./fixture";
import type { BrandIqReport } from "@/lib/cortex-api";

describe("Page1 (Cover)", () => {
  it("renders the brand subject", () => {
    render(<Page1 report={BRAND_IQ_FIXTURE} />);
    expect(screen.getAllByText("Acme Bank Asia").length).toBeGreaterThan(0);
  });

  it("renders the strategic pull-quote from report.coreJudgement", () => {
    render(<Page1 report={BRAND_IQ_FIXTURE} />);
    // The quote body is the brand-specific coreJudgement synthesis.
    expect(screen.getByText(/三條線並置/)).toBeInTheDocument();
    expect(screen.getByText(/Strategic Pin/i)).toBeInTheDocument();
  });

  it("does NOT render fabricated bank-specific copy in the quote", () => {
    render(<Page1 report={BRAND_IQ_FIXTURE} />);
    // The old prototype copy must be gone.
    expect(screen.queryByText(/不是純網銀/)).not.toBeInTheDocument();
    expect(screen.queryByText(/27\s*年信任資產/)).not.toBeInTheDocument();
  });

  it("omits the pull-quote block entirely when coreJudgement is empty", () => {
    const noJudgement: BrandIqReport = {
      ...BRAND_IQ_FIXTURE,
      coreJudgement: "",
    };
    render(<Page1 report={noJudgement} />);
    expect(screen.queryByText(/Strategic Pin/i)).not.toBeInTheDocument();
  });

  it("renders legend counts from report data", () => {
    render(<Page1 report={BRAND_IQ_FIXTURE} />);
    expect(
      screen.getByText(`產品線 · ${BRAND_IQ_FIXTURE.productLines.length}`),
    ).toBeInTheDocument();
    expect(
      screen.getByText(`媒體節點 · ${BRAND_IQ_FIXTURE.mediaNetwork.length}`),
    ).toBeInTheDocument();
  });

  it("renders the cover contents strip from the SECTIONS catalog", () => {
    render(<Page1 report={BRAND_IQ_FIXTURE} />);
    // Cover highlights SEC 01–05 (pages 2–6).
    expect(screen.getByText("SEC · 01")).toBeInTheDocument();
    expect(screen.getByText("SEC · 05")).toBeInTheDocument();
    // p.02 reference for the first highlighted section (品牌核心 = page 2).
    expect(screen.getByText("p.02")).toBeInTheDocument();
  });
});
