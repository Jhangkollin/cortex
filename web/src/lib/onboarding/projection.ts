/**
 * SP-3 projection layer: snake_case `BrandProfileResponse` (cortex-api
 * `cortex-brand-extract`) → camelCase UI `ExtractedBrand`.
 *
 * Owned by SP-3 — SP-1/SP-2 stay UI-agnostic. The backend DTO is NOT a 1:1
 * passthrough: it is snake_case, omits UI-only fields (`id`, `picked`,
 * `icon`) and derived counts (`productMoreCount`), and has nullable strings.
 * This module does the casing, null-coalescing, UI-field synthesis, and
 * `productMoreCount` derivation.
 */

import { VOICE_TONES } from "@/components/onboarding-v2/data";
import type {
  Competitor,
  ExtractedBrand,
  LiveQuestion,
  Media,
  Product,
  VoiceSample,
  VoiceTone,
} from "@/components/onboarding-v2/data";
import type {
  BrandProfileResponse,
  BrandVoiceDTO,
  MediaNetworkDTO,
  WeeklyQuestionsDTO,
} from "@/lib/cortex-api";

export const VISIBLE_PRODUCTS = 2;

const s = (v: string | null | undefined): string => v ?? "";
const slug = (v: string, i: number): string =>
  `${v
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "")}-${i}`;

export function toExtractedBrand(p: BrandProfileResponse): ExtractedBrand {
  const products: Product[] = (p.products ?? []).map((raw, i) => {
    const r = raw as {
      name: string;
      category: string;
      url: string | null;
      confidence: number;
    };
    return {
      id: slug(r.name || "product", i),
      name: r.name,
      category: r.category,
      url: s(r.url),
      icon: "inventory_2",
      picked: i < VISIBLE_PRODUCTS,
      confidence: r.confidence ?? 0,
    };
  });
  const competitors: Competitor[] = (p.competitors ?? []).map((raw, i) => {
    const r = raw as {
      name: string;
      domain: string | null;
      match_score: number;
    };
    return {
      id: slug(r.name || "competitor", i),
      name: r.name,
      domain: s(r.domain),
      picked: true,
      matchScore: r.match_score ?? 0,
    };
  });
  const voiceSamples: VoiceSample[] = (p.voice_samples ?? []).map((raw) => {
    const r = raw as { src: string; text: string };
    return { src: r.src, text: r.text, picked: true };
  });
  return {
    url: s(p.source_url) || s(p.name),
    name: s(p.name),
    legalName: s(p.legal_name),
    tagline: s(p.tagline),
    monogram: s(p.monogram),
    brandColor: s(p.brand_color),
    category: {
      value: s(p.category_value),
      confidence: p.category_confidence ?? 0,
      alternatives: p.category_alternatives ?? [],
    },
    region: p.region ?? [],
    founded: s(p.founded),
    about: s(p.about),
    voiceSamples,
    products,
    productMoreCount: Math.max(0, products.length - VISIBLE_PRODUCTS),
    competitors,
  };
}

// ---------------------------------------------------------------------------
// SP-MEDIA projection: MediaNetworkDTO → Media[]
// ---------------------------------------------------------------------------

export function projectMediaNetwork(dto: MediaNetworkDTO): Media[] {
  return dto.outlets.map((o, i) => ({
    id: o.hostname,
    name: o.member_name || o.hostname,
    audience: o.audience_descriptor,
    weeklyReaders: o.wau,
    contextAgent: o.context_agent_label,
    relevance: o.relevance,
    picked: i < 6,
    topics: o.topics,
    trend: "flat" as const,
  }));
}

// ---------------------------------------------------------------------------
// SP-VOICE projection: BrandVoiceDTO → VoiceTone[]
// ---------------------------------------------------------------------------

export function projectVoiceTones(dto: BrandVoiceDTO): VoiceTone[] {
  return VOICE_TONES.map((t) => ({
    ...t,
    sample:
      dto.samples?.[t.id] && String(dto.samples[t.id]).trim()
        ? dto.samples[t.id]
        : t.sample,
  }));
}

// ---------------------------------------------------------------------------
// SP-QUESTIONS projection: WeeklyQuestionsDTO → LiveQuestion[]
// ---------------------------------------------------------------------------

export function projectWeeklyQuestions(dto: WeeklyQuestionsDTO): LiveQuestion[] {
  return dto.questions.map((q) => ({
    id: q.id,
    text: q.text,
    media: q.media,
    intent: (["Explore", "Understand", "Evaluate", "Act"].includes(q.intent)
      ? q.intent
      : "Understand") as LiveQuestion["intent"],
    score: q.score,
    asks: q.asks ?? 0,
    when: q.when || "—",
    competitorMentions: q.competitorMentions ?? [],
  }));
}
