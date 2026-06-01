/**
 * Page4 (媒體網絡) unit tests.
 * Validates: data-driven media table renders; the fabricated "戰略要點 · So
 * what?" takeaway (a conclusion not in the report contract) has been removed.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Page4 } from "../pages/page-4";
import { BRAND_IQ_FIXTURE } from "./fixture";
import type { BrandIqReport } from "@/lib/cortex-api";

describe("Page4 (媒體網絡)", () => {
  it("renders the section heading", () => {
    render(<Page4 report={BRAND_IQ_FIXTURE} />);
    expect(screen.getByText("你的品牌能被聽見的地方")).toBeInTheDocument();
  });

  it("renders each media outlet name from report data", () => {
    render(<Page4 report={BRAND_IQ_FIXTURE} />);
    BRAND_IQ_FIXTURE.mediaNetwork.forEach((m) => {
      expect(screen.getByText(m.name)).toBeInTheDocument();
    });
  });

  it("does NOT render the fabricated strategy takeaway callout", () => {
    render(<Page4 report={BRAND_IQ_FIXTURE} />);
    expect(screen.queryByText(/戰略要點/)).not.toBeInTheDocument();
    expect(screen.queryByText(/高相關性媒體是品牌可控/)).not.toBeInTheDocument();
  });

  it("renders 資料不足 chip when media network is empty", () => {
    const empty: BrandIqReport = { ...BRAND_IQ_FIXTURE, mediaNetwork: [] };
    render(<Page4 report={empty} />);
    expect(screen.getAllByText("資料不足").length).toBeGreaterThan(0);
  });
});
