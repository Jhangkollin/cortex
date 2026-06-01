/**
 * Pricing tiers — single source of truth.
 *
 * Read by /pricing (V1 cards) and, when V3 ships, by /pricing/compare and the
 * tier × capability drift CI check (see handoff §V3 spec note). Mutating a
 * tier here is the only correct way to change a public price.
 */

export type TierId = "dev" | "pro" | "ent";

export interface FeatureCheck {
  label: string;
  included: boolean;
}

export interface Meter {
  id: string;
  label: string;
  included: number;
  unit: string;
}

export interface Tier {
  id: TierId;
  name: string;
  who: string;
  price: { monthly: number; annual: number };
  unit: "seat";
  minSeats: number | null;
  popular: boolean;
  features: FeatureCheck[];
  meters: Meter[];
  cta: { kind: "stripe" | "sales"; label: string };
  priceHelp: string;
  ctaHelp: string;
}

export function annualPrice(monthly: number): number {
  return Math.round(monthly * 0.8);
}

export const TIERS: readonly Tier[] = [
  {
    id: "dev",
    name: "Developer",
    who: "For builders integrating Cortex into a product or platform.",
    price: { monthly: 20, annual: annualPrice(20) },
    unit: "seat",
    minSeats: 1,
    popular: false,
    features: [
      { label: "Unified API gateway (1 endpoint, 5+ models)", included: true },
      { label: "10K LLM requests / seat / mo", included: true },
      { label: "Decision history · 30 days", included: true },
      { label: "Community Slack support", included: true },
      { label: "No Brand Analytics · No KB", included: false },
    ],
    meters: [],
    cta: { kind: "stripe", label: "Start with Developer" },
    priceHelp: "Billed monthly · cancel anytime",
    ctaHelp: "No credit card required to try",
  },
  {
    id: "pro",
    name: "Pro",
    who: "For brand and content teams shipping into production.",
    price: { monthly: 50, annual: annualPrice(50) },
    unit: "seat",
    minSeats: 5,
    popular: true,
    features: [
      { label: "Everything in Developer", included: true },
      { label: "Brand Analytics + Funnel", included: true },
      {
        label: "Audience Finder + Lead Pilot (CPL billed separately)",
        included: true,
      },
      { label: "100K LLM requests / seat / mo", included: true },
      { label: "SSO · audit log · priority support", included: true },
      { label: "No Knowledge Base · No Nexus advanced", included: false },
    ],
    meters: [],
    cta: { kind: "stripe", label: "Start Pro trial — 14 days" },
    priceHelp: "5-seat minimum · monthly or annual",
    ctaHelp: "Then $50 / seat / mo · 5 seat min",
  },
  {
    id: "ent",
    name: "Enterprise",
    who: "For brands operating at scale across regions and compliance frameworks.",
    price: { monthly: 200, annual: annualPrice(200) },
    unit: "seat",
    minSeats: null,
    popular: false,
    features: [
      { label: "Everything in Pro", included: true },
      { label: "Knowledge Base (vector search, your data)", included: true },
      { label: "Nexus advanced — multi-CDN routing", included: true },
      { label: "Dedicated CSM · 99.95% SLA · DPA", included: true },
      { label: "Custom usage commits · volume discount", included: true },
    ],
    meters: [],
    cta: { kind: "sales", label: "Talk to sales" },
    priceHelp: "Annual contract · custom usage commits",
    ctaHelp: "Pilots ship in < 2 weeks",
  },
];

export function getTier(id: TierId): Tier {
  const tier = TIERS.find((t) => t.id === id);
  if (!tier) throw new Error(`Unknown tier id: ${id}`);
  return tier;
}
