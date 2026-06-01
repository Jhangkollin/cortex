import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { StepComplete } from "../step-complete";

// Minimal brand stub matching the real ExtractedBrand shape.
const brand = {
  url: "daohe.academy",
  name: "Daohe Academy",
  legalName: "Daohe Academy Ltd.",
  tagline: "Learning, redesigned.",
  monogram: "D",
  brandColor: "#1C726B",
  category: { value: "Education", confidence: 95, alternatives: [] },
  region: ["Taiwan"],
  founded: "2020",
  about: "Online education platform.",
  voiceSamples: [],
  products: [{ id: "p1", name: "Khaki Field", category: "Course", url: "/courses/khaki", icon: "school", picked: true, confidence: 95 }],
  productMoreCount: 0,
  competitors: [],
} as never;

const brandsTwo = [
  { id: "brand-hamilton", display_name: "Hamilton", domain: null, role: "admin", onboarded_at: "2026-05-25T00:00:00Z", created_at: "2026-05-20T00:00:00Z", updated_at: "2026-05-25T00:00:00Z" },
  { id: "brand-daohe",    display_name: "Daohe Academy", domain: null, role: "admin", onboarded_at: null, created_at: "2026-05-26T00:00:00Z", updated_at: "2026-05-26T00:00:00Z" },
] as never;

describe("StepComplete (zh) — multi-brand variant", () => {
  it("collapses to single-brand hero when brand_count === 1", () => {
    render(
      <StepComplete
        brand={brand}
        pickedMedia={[]}
        mediaNetwork={[]}
        brands={[brandsTwo[1]]}
        justOnboardedBrandId="brand-daohe"
        onAddBrand={vi.fn()}
        onRestart={vi.fn()}
        onEnterDiscover={vi.fn()}
      />,
    );
    // Single-brand fallback: the existing zh hero text is present
    expect(screen.getByText(/Agent 開始工作了/i)).toBeInTheDocument();
    // No portfolio band heading
    expect(screen.queryByRole("heading", { name: /your portfolio/i })).not.toBeInTheDocument();
    // No "新增品牌" secondary CTA card button
    expect(screen.queryByRole("button", { name: /新增品牌/i })).not.toBeInTheDocument();
  });

  it("shows portfolio band + '新增品牌' CTA when brand_count >= 2", () => {
    const onAddBrand = vi.fn();
    render(
      <StepComplete
        brand={brand}
        pickedMedia={[]}
        mediaNetwork={[]}
        brands={brandsTwo}
        justOnboardedBrandId="brand-daohe"
        onAddBrand={onAddBrand}
        onRestart={vi.fn()}
        onEnterDiscover={vi.fn()}
      />,
    );
    expect(screen.getByText(/Daohe Academy 加入了你的品牌組合/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /^your portfolio/i })).toBeInTheDocument();
    // NEW pip is on the just-onboarded brand only
    expect(screen.getAllByText("NEW").length).toBe(1);
    // Click the secondary CTA card button
    fireEvent.click(screen.getByRole("button", { name: /新增品牌/i }));
    expect(onAddBrand).toHaveBeenCalledTimes(1);
  });
});
