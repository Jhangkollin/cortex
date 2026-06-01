import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StepQuestions } from "@/components/onboarding-v2/step-questions";

// Minimal ExtractedBrand stub — StepQuestions only reads .url
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

describe("StepQuestions — real prop", () => {
  it("renders real questions, never the old LIVE_QUESTIONS mock constant", () => {
    render(
      <StepQuestions
        brand={BRAND_STUB as never}
        liveQuestions={[
          {
            id: "a",
            text: "REALQ?",
            media: "CMoney",
            intent: "Evaluate",
            score: 90,
            asks: 300,
            when: "—",
            competitorMentions: [],
          },
        ]}
      />,
    );
    expect(screen.getByText(/REALQ\?/)).toBeInTheDocument();
    // "Which bank has the lowest fees for overseas salary deposits" is a genuine
    // LIVE_QUESTIONS mock question text that should NOT appear when real data is passed.
    expect(
      screen.queryByText(/Which bank has the lowest fees for overseas salary deposits/),
    ).toBeNull();
  });
});
