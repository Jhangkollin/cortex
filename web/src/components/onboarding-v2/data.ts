/**
 * Mock data backing the v2 onboarding journey.
 *
 * Mirrors the design handoff bundle (cortex/project/onboarding/onb-data.jsx)
 * but with English copy to match the rest of cortex-web. Everything here is
 * client-only — no backend wiring. When a real crawler / brand_profile
 * service lands, swap these constants for the API response shape.
 */

export type CrawlTask = {
  id: string;
  label: string;
  detail: string;
  icon: string;
  delay: number;
};

export const CRAWL_TASKS: CrawlTask[] = [
  { id: "fetch", label: "Fetch homepage", detail: "acmebank.asia · 200 OK", icon: "language", delay: 600 },
  { id: "meta", label: "Read metadata", detail: "title, og:image, schema.org", icon: "code", delay: 700 },
  { id: "logo", label: "Identify brand mark", detail: "Logo / favicon / Apple touch", icon: "interests", delay: 800 },
  { id: "products", label: "Scan product pages", detail: "Parsed 12 product pages", icon: "category", delay: 1000 },
  { id: "category", label: "Infer category", detail: "Retail banking · 96% confidence", icon: "psychology", delay: 700 },
  { id: "voice", label: "Extract brand voice", detail: "47 samples from About + Press", icon: "campaign", delay: 800 },
  { id: "competitors", label: "Match competitors", detail: "4 peers in the same category", icon: "groups", delay: 700 },
  { id: "done", label: "Done", detail: "Everything is editable on the next step", icon: "task_alt", delay: 600 },
];

export type Product = {
  id: string;
  name: string;
  category: string;
  url: string;
  icon: string;
  picked: boolean;
  confidence: number;
};

export type VoiceSample = {
  src: string;
  text: string;
  picked: boolean;
};

export type Competitor = {
  id: string;
  name: string;
  domain: string;
  picked: boolean;
  matchScore: number;
};

export type ExtractedBrand = {
  url: string;
  name: string;
  legalName: string;
  tagline: string;
  monogram: string;
  brandColor: string;
  category: { value: string; confidence: number; alternatives: string[] };
  region: string[];
  founded: string;
  about: string;
  voiceSamples: VoiceSample[];
  products: Product[];
  productMoreCount: number;
  competitors: Competitor[];
};

export const EXTRACTED_BRAND: ExtractedBrand = {
  url: "acmebank.asia",
  name: "Acme Bank Asia",
  legalName: "Acme Bank Asia Holdings, Ltd.",
  tagline: "Banking, redesigned for Asia.",
  monogram: "A",
  brandColor: "#225D59",
  category: {
    value: "Retail banking / Digital banking",
    confidence: 96,
    alternatives: ["Financial services", "FinTech platform"],
  },
  region: ["Taiwan", "Hong Kong", "Singapore"],
  founded: "1998",
  about:
    "For 27 years, Acme Bank Asia has helped over 3.2 million households and businesses across Asia — redesigning banking from a tedious process into a conversation worth trusting.",
  voiceSamples: [
    { src: "/about", text: "Banking should work for people, not the other way around.", picked: true },
    { src: "/press/2025-q4", text: "Every financial decision deserves an advisor behind it.", picked: true },
    { src: "/blog/asia-2026", text: "Asia's next wave of growth comes from the under-served middle.", picked: false },
    { src: "/about", text: "For 27 years, we've supported 3.2 million households across Asia.", picked: true },
  ],
  products: [
    { id: "p1", name: "Acme World Elite Card", category: "Credit card", url: "/credit-cards/world-elite", icon: "credit_card", picked: true, confidence: 98 },
    { id: "p2", name: "Smart Digital Account", category: "Deposits", url: "/accounts/smart", icon: "savings", picked: true, confidence: 97 },
    { id: "p3", name: "First-Home Mortgage 2026", category: "Mortgage", url: "/mortgages/first-home", icon: "home_work", picked: true, confidence: 94 },
    { id: "p4", name: "Acme High-Yield Growth ETF", category: "Investing", url: "/investments/etf-growth", icon: "trending_up", picked: true, confidence: 92 },
    { id: "p5", name: "Multi-currency Deposit", category: "FX", url: "/accounts/fx", icon: "currency_exchange", picked: true, confidence: 91 },
    { id: "p6", name: "Salary-linked Personal Loan", category: "Lending", url: "/loans/salary", icon: "request_quote", picked: true, confidence: 88 },
    { id: "p7", name: "Premier Private Banking", category: "Wealth", url: "/private/premier", icon: "diamond", picked: false, confidence: 78 },
  ],
  productMoreCount: 5,
  competitors: [
    { id: "c1", name: "Cathay United", domain: "cathaybk.com.tw", picked: true, matchScore: 94 },
    { id: "c2", name: "E.Sun Bank", domain: "esunbank.com.tw", picked: true, matchScore: 91 },
    { id: "c3", name: "Taishin Bank", domain: "taishinbank.com.tw", picked: true, matchScore: 88 },
    { id: "c4", name: "CTBC Bank", domain: "ctbcbank.com", picked: false, matchScore: 84 },
  ],
};

export type Media = {
  id: string;
  name: string;
  audience: string;
  weeklyReaders: number | null;
  contextAgent: string;
  relevance: number;
  picked: boolean;
  topics: string[];
  trend: "up" | "down" | "flat";
};

export const MEDIA_NETWORK: Media[] = [
  { id: "moneydj", name: "MoneyDJ", audience: "Investing decision-makers", weeklyReaders: 1_200_000, contextAgent: "Investing Context", relevance: 94, picked: true, topics: ["ETF", "FX", "Dividend stocks"], trend: "up" },
  { id: "smart", name: "Smart Wealth Monthly", audience: "Middle-income families", weeklyReaders: 680_000, contextAgent: "Wealth Planning Context", relevance: 91, picked: true, topics: ["Deposits", "Retirement", "Insurance"], trend: "up" },
  { id: "cw", name: "CommonWealth · Finance", audience: "Owners & professionals", weeklyReaders: 2_100_000, contextAgent: "Macro Finance Context", relevance: 88, picked: true, topics: ["Economy", "Mortgage", "Corporate"], trend: "flat" },
  { id: "bw", name: "Business Weekly", audience: "Management, 40+", weeklyReaders: 1_700_000, contextAgent: "Business Context", relevance: 84, picked: true, topics: ["Credit cards", "High net worth"], trend: "up" },
  { id: "techorange", name: "TechOrange", audience: "Tech workers", weeklyReaders: 540_000, contextAgent: "FinTech Context", relevance: 76, picked: true, topics: ["Digital banking", "Payments", "API"], trend: "up" },
  { id: "yahoo", name: "Yahoo Finance TW", audience: "General consumers", weeklyReaders: 3_400_000, contextAgent: "Mass Consumer Context", relevance: 72, picked: true, topics: ["Card rewards", "Loans"], trend: "flat" },
  { id: "ctee", name: "Commercial Times", audience: "Business decision-makers", weeklyReaders: 890_000, contextAgent: "B2B Finance Context", relevance: 68, picked: false, topics: ["Corporate lending", "FX hedging"], trend: "down" },
  { id: "stockfeel", name: "StockFeel", audience: "Young investors", weeklyReaders: 420_000, contextAgent: "Retail Investor Context", relevance: 64, picked: false, topics: ["Beginner investing", "ETF"], trend: "up" },
];

export type LiveQuestion = {
  id: string;
  text: string;
  media: string;
  intent: "Explore" | "Understand" | "Evaluate" | "Act";
  score: number;
  asks: number;
  when: string;
  competitorMentions: string[];
};

export const LIVE_QUESTIONS: LiveQuestion[] = [
  { id: "q1", text: "Which bank has the lowest fees for overseas salary deposits with direct FX conversion?", media: "MoneyDJ", intent: "Evaluate", score: 92, asks: 1240, when: "2 hours ago", competitorMentions: ["Cathay United", "CTBC"] },
  { id: "q2", text: "Dividend ETFs vs. fixed deposits — which is the right call this year if I'm worried about rates?", media: "Smart Wealth Monthly", intent: "Understand", score: 88, asks: 2310, when: "5 hours ago", competitorMentions: ["Yuanta", "Cathay"] },
  { id: "q3", text: "Looking to buy at 30 — which bank offers the longest grace period on first-home mortgages?", media: "CommonWealth", intent: "Act", score: 86, asks: 870, when: "Today 09:14", competitorMentions: ["E.Sun", "Taishin"] },
  { id: "q4", text: "Is Cathay still the best card for overseas spending rewards?", media: "Yahoo Finance", intent: "Evaluate", score: 81, asks: 1840, when: "Yesterday", competitorMentions: ["Cathay United"] },
  { id: "q5", text: "Which digital accounts pair well with brokerages for the smoothest onboarding?", media: "TechOrange", intent: "Explore", score: 74, asks: 620, when: "2 days ago", competitorMentions: ["Next Bank"] },
  { id: "q6", text: "USD deposit rates are much higher than TWD — should I just move everything across?", media: "MoneyDJ", intent: "Understand", score: 82, asks: 990, when: "4 hours ago", competitorMentions: ["Cathay", "Taishin"] },
];

export const INTENT_COLOR = {
  Explore: { bg: "#E0F2F1", fg: "#00695C" },
  Understand: { bg: "#E3F2FD", fg: "#0D47A1" },
  Evaluate: { bg: "#FFF8E1", fg: "#8D6E00" },
  Act: { bg: "#FFEBEE", fg: "#B71C1C" },
} as const;

// Light Edition (2026-05-27): trimmed demo list to the two brands the
// prototype actually validates against (handoff Appendix C). When a real
// hot-brand API lands, source from the backend instead.
export const URL_SUGGESTIONS = ["mlytics.com", "moonbeam.io"];

export type VoiceTone = {
  id: "expert" | "warm" | "playful";
  label: string;
  desc: string;
  icon: string;
  sample: string;
};

export const VOICE_TONES: VoiceTone[] = [
  {
    id: "expert",
    label: "Expert advisor",
    desc: "Objective, data-led",
    icon: "school",
    sample:
      "If your salary is paid in USD or CNY, the Smart Digital Account from Acme Bank Asia waives fees on the first 5 overseas inbound transfers each month, and converts at rates ~12 bps better than the market mid. For salary-deposit customers above USD 50k/mo, pair with our Multi-currency Deposit to dollar-cost-average your FX exposure — modelled annualised pickup ~0.8%.",
  },
  {
    id: "warm",
    label: "Warm & human",
    desc: "Close, empathetic",
    icon: "favorite",
    sample:
      "If you're paid in a foreign currency every month, you've probably watched the FX fee chip away at your salary — that's completely normal. Our Smart Digital Account waives fees on the first 5 overseas deposits each month, with rates a touch better than the street. For someone on a long-running salary line, what you save over a year really starts to add up.",
  },
  {
    id: "playful",
    label: "Lively & direct",
    desc: "Young, conversational",
    icon: "celebration",
    sample:
      "Hey — the worst part of an overseas paycheck is watching FX skim a layer off the top. Smart Digital Account waives the first 5 overseas deposits a month, and the rate is on the sweet side. If math isn't your thing, just use it. What it saves you is exactly what others are still arguing about.",
  },
];

export type DeployAgent = {
  id: string;
  name: string;
  kind: "context" | "core";
  icon: string;
};

export const DEPLOY_AGENTS: DeployAgent[] = [
  { id: "context-moneydj", name: "Context Agent · MoneyDJ", kind: "context", icon: "hub" },
  { id: "context-smart", name: "Context Agent · Smart Wealth", kind: "context", icon: "hub" },
  { id: "context-cw", name: "Context Agent · CommonWealth", kind: "context", icon: "hub" },
  { id: "context-bw", name: "Context Agent · Business Weekly", kind: "context", icon: "hub" },
  { id: "context-tech", name: "Context Agent · TechOrange", kind: "context", icon: "hub" },
  { id: "context-yahoo", name: "Context Agent · Yahoo Finance", kind: "context", icon: "hub" },
  { id: "answer-pilot", name: "Answer Pilot", kind: "core", icon: "edit_note" },
  { id: "geo-pilot", name: "GEO Pilot · Distribution", kind: "core", icon: "explore" },
  { id: "monetize-lens", name: "Monetize Lens · Attribution", kind: "core", icon: "insights" },
  { id: "market-radar", name: "Market Radar · Competitive", kind: "core", icon: "radar" },
];

export type DeployLogLine = { t: string; text: string; status: "OK" | "DONE" };

export const DEPLOY_LOG: DeployLogLine[] = [
  { t: "+00s", text: "Authorize Context Agent access to media-network API…", status: "OK" },
  { t: "+01s", text: "Upload Brand Profile: Acme Bank Asia", status: "OK" },
  { t: "+02s", text: "Load 6 product KB cards", status: "OK" },
  { t: "+03s", text: "Calibrate Brand Voice fingerprint (4 training samples)", status: "OK" },
  { t: "+05s", text: "Deploy Context Agent · MoneyDJ → ap-tw-1", status: "OK" },
  { t: "+06s", text: "Deploy Context Agent · Smart Wealth → ap-tw-1", status: "OK" },
  { t: "+07s", text: "Deploy Context Agent · CommonWealth → ap-tw-1", status: "OK" },
  { t: "+08s", text: "Deploy Context Agent · Business Weekly → ap-tw-1", status: "OK" },
  { t: "+09s", text: "Deploy Context Agent · TechOrange → ap-tw-1", status: "OK" },
  { t: "+10s", text: "Deploy Context Agent · Yahoo → ap-tw-2", status: "OK" },
  { t: "+12s", text: "Answer Pilot standby · subscribed to weekly question queue", status: "OK" },
  { t: "+13s", text: "GEO Pilot online · 4 distribution channels", status: "OK" },
  { t: "+14s", text: "Monetize Lens online · click attribution active", status: "OK" },
  { t: "+15s", text: "Market Radar online · monitoring 4 competitors", status: "OK" },
  { t: "+16s", text: "First batch dispatched · 5 high-intent items entered draft queue", status: "OK" },
  { t: "+17s", text: "Brand Agent fully online · ready", status: "DONE" },
];

export const RAIL_STEPS = [
  "Connect site",
  "Confirm brand",
  "Media network",
  "Weekly questions",
  "Launch Agent",
  "Done",
] as const;

export type RailIndex = 0 | 1 | 2 | 3 | 4 | 5;

// Internal step numbering:
//   0 = welcome (rail 0)
//   1 = crawl   (rail 0)
//   2 = review  (rail 1)
//   3 = media   (rail 2)
//   4 = questions (rail 3)
//   5 = launch settings (rail 4)
//   6 = launching overlay (rail 4)
//   7 = complete (rail 5)
export type InternalStep = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7;

export function railFor(step: InternalStep): RailIndex {
  if (step <= 1) return 0;
  if (step === 6) return 4;
  if (step >= 7) return 5;
  return (step - 1) as RailIndex;
}
