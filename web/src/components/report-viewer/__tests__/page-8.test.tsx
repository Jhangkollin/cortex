/**
 * Page8 (風險 + 來源 + 品質) unit tests.
 * Validates: risk rendering, 資料不足 for empty sources.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Page8 } from "../pages/page-8";
import { BRAND_IQ_FIXTURE } from "./fixture";
import type { BrandIqReport } from "@/lib/cortex-api";

describe("Page8 (風險 + 來源 + 品質)", () => {
  it("renders the compliance signals heading", () => {
    render(<Page8 report={BRAND_IQ_FIXTURE} />);
    expect(screen.getByText("合規風險訊號")).toBeInTheDocument();
  });

  it("renders all risk theme names", () => {
    render(<Page8 report={BRAND_IQ_FIXTURE} />);
    BRAND_IQ_FIXTURE.risks.forEach((r) => {
      expect(screen.getByText(r.theme)).toBeInTheDocument();
    });
  });

  it("renders 高 風險 badge for high risks", () => {
    render(<Page8 report={BRAND_IQ_FIXTURE} />);
    const highBadges = screen.getAllByText("高 風險");
    expect(highBadges.length).toBeGreaterThan(0);
  });

  it("renders 中 風險 badge for medium risks", () => {
    render(<Page8 report={BRAND_IQ_FIXTURE} />);
    const midBadges = screen.getAllByText("中 風險");
    expect(midBadges.length).toBeGreaterThan(0);
  });

  it("renders source A items", () => {
    render(<Page8 report={BRAND_IQ_FIXTURE} />);
    expect(screen.getByText(/acmebank\.asia/)).toBeInTheDocument();
  });

  it("renders data quality section", () => {
    render(<Page8 report={BRAND_IQ_FIXTURE} />);
    expect(screen.getByText("資料品質評估")).toBeInTheDocument();
  });

  it("renders 資料不足 chip for empty source A list", () => {
    const emptySourceReport: BrandIqReport = {
      ...BRAND_IQ_FIXTURE,
      sources: {
        A: [],
        B: BRAND_IQ_FIXTURE.sources.B,
        C: BRAND_IQ_FIXTURE.sources.C,
      },
    };
    render(<Page8 report={emptySourceReport} />);
    const chips = screen.getAllByText("資料不足");
    expect(chips.length).toBeGreaterThan(0);
  });

  it("renders 資料不足 chip for empty risks list", () => {
    const emptyRisksReport: BrandIqReport = {
      ...BRAND_IQ_FIXTURE,
      risks: [],
    };
    render(<Page8 report={emptyRisksReport} />);
    const chips = screen.getAllByText("資料不足");
    expect(chips.length).toBeGreaterThan(0);
  });
});
