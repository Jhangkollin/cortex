import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StepMedia } from "@/components/onboarding-v2/step-media";

const REAL = [
  {
    id: "aigc.cmoney.tw",
    name: "CMoney",
    audience: "Investors",
    weeklyReaders: 117260,
    contextAgent: "Wealth",
    relevance: 91,
    picked: true,
    topics: ["ETF"],
    trend: "flat" as const,
  },
];

// Minimal ExtractedBrand stub — StepMedia only reads .category.value, .region, and .competitors
const BRAND_STUB = {
  url: "stub.test",
  name: "Stub Brand",
  legalName: "",
  tagline: "",
  monogram: "S",
  brandColor: "#000",
  category: { value: "Banking", confidence: 90, alternatives: [] },
  region: ["Taiwan"],
  founded: "2000",
  about: "",
  voiceSamples: [],
  products: [],
  productMoreCount: 0,
  competitors: [],
};

describe("StepMedia — real network", () => {
  it("renders real catalog names, never the old mock constant", () => {
    render(
      <StepMedia
        brand={BRAND_STUB}
        picked={[]}
        setPicked={() => {}}
        mediaNetwork={REAL}
      />,
    );
    expect(screen.getByText("CMoney")).toBeInTheDocument();
    // "Smart Wealth Monthly" is a genuine MEDIA_NETWORK mock outlet name
    // that should NOT appear when real data is passed.
    expect(screen.queryByText("Smart Wealth Monthly")).toBeNull();
  });
});
