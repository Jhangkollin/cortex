import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { ExtractedBrand } from "@/components/onboarding-v2-zh/data";
import { StepLaunch } from "@/components/onboarding-v2-zh/step-launch";

const VOICE_TONES = [
  {
    id: "expert" as const,
    label: "專家顧問",
    desc: "精準、具公信力、以引用為本",
    icon: "school",
    sample: "REALVOICE_SENTINEL",
  },
  {
    id: "warm" as const,
    label: "溫暖嚮導",
    desc: "安心、貼近人",
    icon: "favorite",
    sample: "Warm sample copy.",
  },
  {
    id: "playful" as const,
    label: "活潑同伴",
    desc: "輕鬆、有活力",
    icon: "mood",
    sample: "Playful sample copy.",
  },
];

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
    text: "LOWSCORE_SENTINEL 比較不相關的問題？",
    media: "SideBlog",
    intent: "Explore" as const,
    score: 40,
    asks: 12,
    when: "3 天前",
    competitorMentions: [],
  },
  {
    id: "q-top",
    text: "TOPQ_SENTINEL 讀者真正在問這個品牌的什麼？",
    media: "TechCrunch",
    intent: "Evaluate" as const,
    score: 95,
    asks: 500,
    when: "1 小時前",
    competitorMentions: [],
  },
];

// The hardcoded zh banking mock that must never render.
const HARDCODED_BANKING_Q = /海外薪轉戶/;

describe("StepLaunch (zh) — real reader question (not hardcoded mock)", () => {
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
    expect(screen.getByText(/1 小時前/)).toBeInTheDocument();
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
    expect(screen.queryByText(/Smart 數位帳戶/)).not.toBeInTheDocument();
    expect(screen.queryByText(/外幣綜合存款/)).not.toBeInTheDocument();
  });
});
