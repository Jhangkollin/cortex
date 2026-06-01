import { describe, expect, it } from "vitest";

import type { BrandProfileResponse } from "@/lib/cortex-api";

import {
  projectMediaNetwork,
  projectVoiceTones,
  projectWeeklyQuestions,
  toExtractedBrand,
} from "./projection";

const RESP = {
  brand_id: "b1", name: "Acme Bank", legal_name: null, tagline: null,
  monogram: null, brand_color: null, founded: null, about: null,
  source_url: "acmebank.asia", industry_vertical: null, primary_jurisdiction: null,
  category_value: "Banking", category_confidence: 88, category_alternatives: ["Fintech"],
  region: ["APAC"],
  voice_samples: [{ src: "home", text: "Hi" }],
  products: [
    { name: "Save", category: "Deposit", url: null, confidence: 70 },
    { name: "Loan", category: "Credit", url: null, confidence: 60 },
    { name: "Card", category: "Credit", url: null, confidence: 50 },
  ],
  competitors: [{ name: "C1", domain: "c1.com", match_score: 42 }],
  media_matches: [],
  extraction_meta: null,
  created_at: "2026-05-18T00:00:00Z", updated_at: "2026-05-18T00:00:00Z",
} as unknown as BrandProfileResponse;

describe("toExtractedBrand", () => {
  it("snake to camel, null-coalesce, synth fields, productMoreCount", () => {
    const eb = toExtractedBrand(RESP);
    expect(eb.url).toBe("acmebank.asia");
    expect(eb.name).toBe("Acme Bank");
    expect(eb.legalName).toBe("");
    expect(eb.category).toEqual({ value: "Banking", confidence: 88, alternatives: ["Fintech"] });
    expect(eb.products).toHaveLength(3);
    expect(eb.products[0]).toMatchObject({ name: "Save", picked: true });
    expect(eb.products[0].id).toBeTruthy();
    expect(eb.products[0].icon).toBeTruthy();
    expect(eb.competitors[0].matchScore).toBe(42);
    expect(eb.productMoreCount).toBe(1);
  });
});

it("projectMediaNetwork maps real outlets to Media[]", () => {
  const dto = { brand_id: "b", status: "succeeded", outlets: [
    { hostname: "aigc.cmoney.tw", member_name: "CMoney", wau: 117260, relevance: 91,
      why: "fit", topics: ["a"], context_agent_label: "Wealth Context", audience_descriptor: "Investors" },
  ] };
  const m = projectMediaNetwork(dto);
  expect(m[0].id).toBe("aigc.cmoney.tw");
  expect(m[0].name).toBe("CMoney");
  expect(m[0].weeklyReaders).toBe(117260);
  expect(m[0].relevance).toBe(91);
  expect(m[0].picked).toBe(true);
});

it("projectVoiceTones merges real samples into the VOICE_TONES constants", () => {
  const dto = { brand_id: "b", status: "succeeded",
    samples: { expert: "REAL EXPERT", warm: "REAL WARM" } };  // playful missing
  const t = projectVoiceTones(dto);
  const byId = Object.fromEntries(t.map((x) => [x.id, x]));
  expect(byId.expert.sample).toBe("REAL EXPERT");
  expect(byId.warm.sample).toBe("REAL WARM");
  expect(byId.playful.sample.length).toBeGreaterThan(0);   // fallback to constant sample
  expect(byId.expert.label).toBeTruthy();                  // id/label/desc/icon from constant
});

it("projectWeeklyQuestions maps real questions to LiveQuestion[]", () => {
  const dto = { brand_id: "b", status: "succeeded", questions: [
    { id: "a", text: "Best ETF?", media: "CMoney", asks: 300, when: "2026-05-15",
      intent: "Evaluate", score: 91, competitorMentions: ["Cathay"] }] };
  const q = projectWeeklyQuestions(dto);
  expect(q[0].id).toBe("a");
  expect(q[0].text).toBe("Best ETF?");
  expect(q[0].media).toBe("CMoney");
  expect(q[0].asks).toBe(300);
  expect(q[0].intent).toBe("Evaluate");
  expect(q[0].competitorMentions).toEqual(["Cathay"]);
});
