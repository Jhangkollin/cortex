/**
 * Single source of truth for report-section metadata.
 *
 * Consumed by:
 *   - `report-viewer.tsx`  — TOC list + the page-label-above each artboard
 *   - `page-1.tsx`         — the cover "contents" strip (filters `coverHighlight`)
 *   - `pages/page-N.tsx`   — each page's `<PageHeader>` / `<PageFooter>` strings
 *
 * Pages 7 and 8 span multiple report sections, so the running-header SEC
 * label is NOT derivable from the page number alone — hence it is stored
 * explicitly per entry rather than computed.
 */
export interface ReportSection {
  /** Page number, 1–8 (also the artboard order). */
  n: number;
  /** TOC label (zh). */
  toc: string;
  /** TOC sublabel (en short). */
  tocEn: string;
  /** Running-header SEC label, e.g. "SEC · 01" or "SEC · 06–07". */
  sectionLabel: string;
  /** Running-header en string, e.g. "品牌核心 · The Anatomy". */
  headerEn: string;
  /** Footer left string, e.g. "SEC · 01 — 品牌核心". */
  footerLeft: string;
  /**
   * Whether this section appears in the cover "contents" strip. When true,
   * `coverSec` is the 2-digit section number shown on the cover.
   */
  coverHighlight: boolean;
  /** Cover-strip SEC number (e.g. "01"); present only when coverHighlight. */
  coverSec?: string;
}

export const SECTIONS: ReportSection[] = [
  {
    n: 1,
    toc: "封面",
    tocEn: "Cover",
    sectionLabel: "",
    headerEn: "",
    footerLeft: "",
    coverHighlight: false,
  },
  {
    n: 2,
    toc: "品牌核心",
    tocEn: "Anatomy",
    sectionLabel: "SEC · 01",
    headerEn: "品牌核心 · The Anatomy",
    footerLeft: "SEC · 01 — 品牌核心",
    coverHighlight: true,
    coverSec: "01",
  },
  {
    n: 3,
    toc: "產品線結構",
    tocEn: "Portfolio",
    sectionLabel: "SEC · 02",
    headerEn: "產品線結構 · Portfolio",
    footerLeft: "SEC · 02 — 產品線結構",
    coverHighlight: true,
    coverSec: "02",
  },
  {
    n: 4,
    toc: "媒體網絡",
    tocEn: "Galaxy",
    sectionLabel: "SEC · 03",
    headerEn: "媒體網絡 · The Reachable Galaxy",
    footerLeft: "SEC · 03 — 媒體網絡",
    coverHighlight: true,
    coverSec: "03",
  },
  {
    n: 5,
    toc: "競品輪廓",
    tocEn: "Landscape",
    sectionLabel: "SEC · 04",
    headerEn: "競品輪廓 · Competitor Landscape",
    footerLeft: "SEC · 04 — 競品輪廓",
    coverHighlight: true,
    coverSec: "04",
  },
  {
    n: 6,
    toc: "戰略洞察",
    tocEn: "Insights",
    sectionLabel: "SEC · 05",
    headerEn: "戰略洞察 · Strategic Insights",
    footerLeft: "SEC · 05 — 戰略洞察",
    coverHighlight: true,
    coverSec: "05",
  },
  {
    n: 7,
    toc: "讀者熱問+通路",
    tocEn: "FAQ + Channels",
    sectionLabel: "SEC · 06–07",
    headerEn: "Voice in the Wild · 讀者熱問 + 通路布局",
    footerLeft: "SEC · 06–07 — FAQ + Channels",
    coverHighlight: false,
  },
  {
    n: 8,
    toc: "風險+來源+品質",
    tocEn: "Caveats",
    sectionLabel: "SEC · 08–10",
    headerEn: "Caveats · 風險、來源、品質",
    footerLeft: "SEC · 08–10 — Caveats",
    coverHighlight: false,
  },
];

/** Lookup a section by page number. Throws if absent (programmer error). */
export function sectionFor(n: number): ReportSection {
  const s = SECTIONS.find((x) => x.n === n);
  if (!s) throw new Error(`No report section for page ${n}`);
  return s;
}
