import type { RichText } from "./rich-text";

export type AlertKind = "warn" | "opp" | "sig";
export interface Alert { kind: AlertKind; icon: string; cat: string; headline: RichText; sub: string; cta: string; }
export interface Hero { v: string; suffix: string; delta: string; note: string; live: string; }
export interface Mini { lab: string; v: string; note: string; trend: "answers" | "views" | "clicks"; }
export interface FunnelBlock { v: string; nm: RichText; here?: boolean; badge?: string; }
export interface FunnelArrow { rate: string; label: RichText; kind?: "bottleneck" | "leverage"; }
export interface MediaRow { rk: string; nm: string; badge?: string; vis: number; clk: string; }
export interface CompRow { nm: string; pct: number; you?: boolean; lead?: boolean; }
export interface DiscoverData {
  alerts: [Alert, Alert, Alert];
  hero: Hero;
  minis: [Mini, Mini, Mini];
  funnel: { blocks: FunnelBlock[]; arrows: FunnelArrow[]; takeaway: RichText; takeawayCta: string };
  media: { sub: string; rows: MediaRow[] };
  comp: { sub: string; rows: CompRow[]; gap: string };
}
export interface ComposerModel { id: string; name: string; desc: string; icon: string; lat: string; }
