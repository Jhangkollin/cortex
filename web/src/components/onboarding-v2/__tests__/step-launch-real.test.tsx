import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { ExtractedBrand } from "@/components/onboarding-v2/data";
import { StepLaunch } from "@/components/onboarding-v2/step-launch";

// Real VoiceTone shape: { id; label; desc; icon; sample }. The selected
// tone's `sample` is what StepLaunch hot-swaps into the live preview card,
// so a real getVoiceTones() payload must reach the DOM through that path.
const VOICE_TONES = [
  {
    id: "expert" as const,
    label: "Expert advisor",
    desc: "Precise, credentialed, citation-led",
    icon: "school",
    sample: "REALVOICE_SENTINEL",
  },
  {
    id: "warm" as const,
    label: "Warm guide",
    desc: "Reassuring and human",
    icon: "favorite",
    sample: "Warm sample copy.",
  },
  {
    id: "playful" as const,
    label: "Playful peer",
    desc: "Casual and energetic",
    icon: "mood",
    sample: "Playful sample copy.",
  },
];

// Minimal ExtractedBrand stub — StepLaunch reads .products, .competitors,
// .voiceSamples, .brandColor, .monogram, .name.
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

const LIVE_QUESTIONS = [
  {
    id: "q-low",
    text: "LOWSCORE_SENTINEL a less relevant question?",
    media: "SideBlog",
    intent: "Explore" as const,
    score: 40,
    asks: 12,
    when: "3 days ago",
    competitorMentions: [],
  },
  {
    id: "q-top",
    text: "TOPQ_SENTINEL what readers actually ask about this brand?",
    media: "TechCrunch",
    intent: "Evaluate" as const,
    score: 95,
    asks: 500,
    when: "1 hour ago",
    competitorMentions: [],
  },
];

const HARDCODED_BANKING_Q = /lowest fees for overseas salary deposits/;

describe("StepLaunch — real voice tones", () => {
  it("renders the selected tone's real sample copy in the preview", () => {
    render(
      <StepLaunch
        brand={BRAND_STUB}
        pickedMedia={[]}
        voiceTone="expert"
        setVoiceTone={() => {}}
        onLaunch={() => {}}
        mediaNetwork={[]}
        voiceTones={VOICE_TONES}
        liveQuestions={LIVE_QUESTIONS}
      />,
    );
    // The expert tone is selected, so its real sample must reach the DOM.
    expect(screen.getByText("REALVOICE_SENTINEL")).toBeInTheDocument();
  });
});

describe("StepLaunch — real reader question (not hardcoded mock)", () => {
  function renderWith(liveQuestions: typeof LIVE_QUESTIONS, brand: ExtractedBrand = BRAND_STUB) {
    render(
      <StepLaunch
        brand={brand}
        pickedMedia={[]}
        voiceTone="expert"
        setVoiceTone={() => {}}
        onLaunch={() => {}}
        mediaNetwork={[]}
        voiceTones={VOICE_TONES}
        liveQuestions={liveQuestions}
      />,
    );
  }

  it("features the highest-score live question, not the hardcoded banking sample", () => {
    renderWith(LIVE_QUESTIONS);
    expect(screen.getByText(/TOPQ_SENTINEL/)).toBeInTheDocument();
    expect(screen.queryByText(/LOWSCORE_SENTINEL/)).not.toBeInTheDocument();
    expect(screen.queryByText(HARDCODED_BANKING_Q)).not.toBeInTheDocument();
  });

  it("attributes the preview to the real question's media + recency, not 'MoneyDJ'", () => {
    renderWith(LIVE_QUESTIONS);
    expect(screen.getByText(/TechCrunch/)).toBeInTheDocument();
    expect(screen.getByText(/1 hour ago/)).toBeInTheDocument();
    expect(screen.queryByText(/MoneyDJ/)).not.toBeInTheDocument();
  });

  it("never falls back to the hardcoded banking sample when there are no live questions", () => {
    renderWith([]);
    expect(screen.queryByText(HARDCODED_BANKING_Q)).not.toBeInTheDocument();
    expect(screen.queryByText(/MoneyDJ/)).not.toBeInTheDocument();
  });

  it("uses the brand's real products for the citation tags, not hardcoded banking products", () => {
    const brand = {
      ...BRAND_STUB,
      products: [
        { id: "p1", name: "CDN_PRODUCT_SENTINEL", category: "x", url: "", icon: "bolt", picked: true, confidence: 90 },
      ],
    };
    renderWith(LIVE_QUESTIONS, brand);
    expect(screen.getByText(/CDN_PRODUCT_SENTINEL/)).toBeInTheDocument();
    expect(screen.queryByText(/Smart Digital Account/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Multi-currency Deposit/)).not.toBeInTheDocument();
  });
});
