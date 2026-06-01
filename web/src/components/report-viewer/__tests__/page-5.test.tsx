/**
 * Page5 (競品輪廓) unit tests.
 * Validates: real competitor cards render; the fabricated 2×2 scatter (with
 * invented competitor coords/names) has been removed.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Page5 } from "../pages/page-5";
import { BRAND_IQ_FIXTURE } from "./fixture";
import type { BrandIqReport } from "@/lib/cortex-api";

describe("Page5 (競品輪廓)", () => {
  it("renders the section heading", () => {
    render(<Page5 report={BRAND_IQ_FIXTURE} />);
    expect(screen.getByText("你在這個品類的位置")).toBeInTheDocument();
  });

  it("renders each competitor tier and its brands string from report data", () => {
    render(<Page5 report={BRAND_IQ_FIXTURE} />);
    BRAND_IQ_FIXTURE.competitors.forEach((c) => {
      expect(screen.getByText(c.tier)).toBeInTheDocument();
      expect(screen.getByText(c.brands)).toBeInTheDocument();
    });
  });

  it("does NOT render the fabricated 2×2 scatter chart", () => {
    render(<Page5 report={BRAND_IQ_FIXTURE} />);
    expect(screen.queryByText("Relative positioning · 2×2")).not.toBeInTheDocument();
    expect(screen.queryByText("數位優先 ↑")).not.toBeInTheDocument();
    expect(screen.queryByText("顧問式 →")).not.toBeInTheDocument();
    // The invented standalone scatter labels must be gone.
    expect(screen.queryByText("LINE Bank")).not.toBeInTheDocument();
    expect(screen.queryByText("將來銀行")).not.toBeInTheDocument();
  });

  it("renders 資料不足 chip when competitors list is empty", () => {
    const empty: BrandIqReport = { ...BRAND_IQ_FIXTURE, competitors: [] };
    render(<Page5 report={empty} />);
    expect(screen.getAllByText("資料不足").length).toBeGreaterThan(0);
  });
});
