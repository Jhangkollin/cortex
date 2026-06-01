/**
 * Page2 (品牌核心) unit tests.
 * Validates: normal render, 資料不足 honesty marker for empty core list.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Page2 } from "../pages/page-2";
import { BRAND_IQ_FIXTURE } from "./fixture";
import type { BrandIqReport } from "@/lib/cortex-api";

describe("Page2 (品牌核心)", () => {
  it("renders the section heading", () => {
    render(<Page2 report={BRAND_IQ_FIXTURE} />);
    expect(screen.getByText("品牌核心解剖")).toBeInTheDocument();
  });

  it("renders all core items", () => {
    render(<Page2 report={BRAND_IQ_FIXTURE} />);
    BRAND_IQ_FIXTURE.core.forEach((item) => {
      expect(screen.getByText(item.item)).toBeInTheDocument();
    });
  });

  it("renders certainty chips for core items", () => {
    render(<Page2 report={BRAND_IQ_FIXTURE} />);
    // At least the "已確認" chips
    const chips = screen.getAllByText("已確認");
    expect(chips.length).toBeGreaterThan(0);
  });

  it("renders 高可能 chip for items with that certainty", () => {
    render(<Page2 report={BRAND_IQ_FIXTURE} />);
    expect(screen.getByText("高可能")).toBeInTheDocument();
  });

  it("renders the coreJudgement pull quote", () => {
    render(<Page2 report={BRAND_IQ_FIXTURE} />);
    expect(screen.getByText(/三條線並置/)).toBeInTheDocument();
  });

  it("renders 資料不足 chip when core list is empty", () => {
    const emptyReport: BrandIqReport = {
      ...BRAND_IQ_FIXTURE,
      core: [],
    };
    render(<Page2 report={emptyReport} />);
    const chips = screen.getAllByText("資料不足");
    expect(chips.length).toBeGreaterThan(0);
  });

  it("renders the At a glance stats", () => {
    render(<Page2 report={BRAND_IQ_FIXTURE} />);
    expect(screen.getByText("成立")).toBeInTheDocument();
    expect(screen.getByText("主市場")).toBeInTheDocument();
  });

  it("does NOT render the fabricated Voice 樣本 stat", () => {
    render(<Page2 report={BRAND_IQ_FIXTURE} />);
    expect(screen.queryByText("Voice 樣本")).not.toBeInTheDocument();
    expect(screen.queryByText("4 / 47")).not.toBeInTheDocument();
  });

  it("falls back to '—' for missing category (never invents 零售金融)", () => {
    const noCategory: BrandIqReport = {
      ...BRAND_IQ_FIXTURE,
      meta: { ...BRAND_IQ_FIXTURE.meta, category: undefined },
    };
    render(<Page2 report={noCategory} />);
    expect(screen.queryByText("零售金融")).not.toBeInTheDocument();
  });
});
