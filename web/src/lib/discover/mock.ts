import type { ComposerModel, DiscoverData } from "./types";

// BASE_DATA is the canonical v2.1 Discover fixture. QUERY_PRESETS / QUERY_CHIPS
// were retired with the Cortex query strip in v2.1. JSX rich values are
// serialized to RichText (decision 7): a <b>X</b> run becomes { b: "X" };
// a <br /> becomes a "\n" span.

export const BASE_DATA: DiscoverData = {
  alerts: [
    {
      kind: "warn",
      icon: "warning_amber",
      cat: "GAP",
      headline: [{ b: "8 brand answers missing" }, " on tracked questions"],
      sub: "projected loss: ~390 views · ~24 clicks",
      cta: "Fix gaps →",
    },
    {
      kind: "opp",
      icon: "trending_up",
      cat: "WIN",
      headline: [
        { b: "鉅亨網" },
        " drove 142 brand clicks this week — most of any publisher",
      ],
      sub: "4 new related articles, +18 % WoW",
      cta: "Expand Anue coverage →",
    },
    {
      kind: "sig",
      icon: "compare_arrows",
      cat: "WATCH",
      headline: [
        { b: "Competitor A" },
        " widened the gap by +0.4 pp this week",
      ],
      sub: "biggest movement on mortgage · FX clusters",
      cta: "See by cluster →",
    },
  ],
  hero: {
    v: "18.4",
    suffix: "%",
    delta: "▲ 3.1 pp",
    note: "vs previous 30 days · 30-day rolling",
    live: "live · q1,427",
  },
  minis: [
    { lab: "Brand-cited answers", v: "94", note: "+12 this week", trend: "answers" },
    { lab: "Answer views", v: "4,580", note: "↗ 10.4%", trend: "views" },
    { lab: "Brand clicks", v: "284", note: "↗ 8.4%", trend: "clicks" },
  ],
  funnel: {
    blocks: [
      { v: "320", nm: [{ b: "Articles" }, " · indexed"] },
      { v: "890", nm: [{ b: "Questions" }, " · asked"] },
      {
        v: "94",
        nm: [{ b: "Answers" }, " · citing brand"],
        here: true,
        badge: "✦ 18.4% visibility",
      },
      { v: "4,580", nm: [{ b: "Answer" }, " · views"] },
      { v: "284", nm: [{ b: "Brand" }, " · clicks"] },
    ],
    arrows: [
      { rate: "×2.8", label: ["per article"] },
      {
        rate: "11.0%",
        kind: "bottleneck",
        label: [{ b: "bottleneck" }, "\nanswer rate"],
      },
      {
        rate: "49×",
        kind: "leverage",
        label: [{ b: "leverage" }, "\nviews/answer"],
      },
      { rate: "6.2%", label: ["CTR"] },
    ],
    takeaway: [
      "Only ",
      { b: "1 in 9" },
      " questions gets a brand-cited answer. Closing the ",
      { b: "8 missing answers" },
      " Cortex flagged could add ",
      { b: "~390 views" },
      " and ",
      { b: "~24 clicks" },
      " at current ratios.",
    ],
    takeawayCta: "Fix gaps →",
  },
  media: {
    sub: "Five outlets account for 91 % of mentions.",
    rows: [
      { rk: "#1", nm: "鉅亨網", vis: 38, clk: "142" },
      { rk: "#2", nm: "數位時代", vis: 24, clk: "68" },
      { rk: "#3", nm: "CMoney", vis: 19, clk: "52" },
      { rk: "#4", nm: "早安健康", vis: 11, clk: "14" },
      { rk: "#5", nm: "Bella 儂儂", vis: 8, clk: "8" },
    ],
  },
  comp: {
    sub: "Same question set · 30-day window",
    rows: [
      { nm: "Acme Bank Asia", pct: 18.4, you: true },
      { nm: "Competitor A", pct: 34.2, lead: true },
      { nm: "Competitor B", pct: 12.1 },
      { nm: "Competitor C", pct: 8.3 },
    ],
    gap: "−15.8 pp",
  },
};


// Transcribed verbatim from cortex-composer.jsx MODELS (lines 7-12).
export const COMPOSER_MODELS: ComposerModel[] = [
  { id: "gemini-flash", name: "Gemini 2.5 Flash", desc: "Lowest latency, low cost", icon: "bolt", lat: "23ms" },
  { id: "gemini-pro", name: "Gemini 2.5 Pro", desc: "General reasoning, multimodal", icon: "memory", lat: "84ms" },
  { id: "claude-opus", name: "Claude Opus 4.7", desc: "Highest reasoning quality", icon: "psychology", lat: "312ms" },
  { id: "gpt-5", name: "GPT-5", desc: "Broad capability, tool use", icon: "developer_mode", lat: "156ms" },
];
