import type { RichText } from "./rich-text";

export type AlertKind = "warn" | "opp" | "sig";
export interface Alert { kind: AlertKind; icon: string; cat: string; headline: RichText; sub: string; cta: string; }
export interface Kpi { lab: string; v: string; note: string; trend: "answers" | "views" | "clicks" | "revenue"; }
export interface FunnelBlock { v: string; nm: RichText; here?: boolean; badge?: string; }
export interface FunnelArrow { rate: string; label: RichText; kind?: "bottleneck" | "leverage"; }
export interface MediaRow { nm: string; badge?: string; vis: number; }
export interface IntentCategory { nm: string; count: number; views: number; top?: boolean; }
export interface Question { q: string; views: number; publisher: string; match: string; }
export interface GeoOpportunity { sub: string; tags: string[]; status: string; note: string; }
export interface DiscoverData {
  alerts: [Alert, Alert, Alert];
  kpis: [Kpi, Kpi, Kpi, Kpi];
  funnel: {
    title: string;
    sub: string;
    disclaimer: string;
    blocks: FunnelBlock[];
    arrows: FunnelArrow[];
    takeaway: RichText;
    takeawayCta: string;
  };
  media: { title: string; sub: string; rows: MediaRow[] };
  intent: { rows: IntentCategory[] };
  questions: Question[];
  geo: GeoOpportunity;
}
export interface ComposerModel { id: string; name: string; desc: string; icon: string; lat: string; }
