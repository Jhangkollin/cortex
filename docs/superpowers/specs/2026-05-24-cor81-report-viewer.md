# COR-81: Brand IQ Report Viewer

**Date:** 2026-05-24
**Status:** Implementation
**Branch:** `feature/cor-81-report-viewer`

## Decision

Standard Next.js in-app viewer rendered as a full-screen overlay within the brand shell. Server component fetches the report; client component renders it. No custom PDF library — browser `window.print()` for print, link to the COR-80 PDF endpoint for download.

## Route

`web/src/app/brand/reports/[reportId]/page.tsx`

- Server component
- `auth()` → `brandId = session.user.activeContext.id`
- `fetchBrandReport(brandId, reportId)` from `cortex-api.ts`
- If report is pending/not-ready → renders a loading/status state
- If 404 → renders a not-found state
- If ready → passes `<ReportViewer report={...} />` (client component)

## Component Breakdown

```
web/src/components/report-viewer/
  report-viewer.tsx           ← "use client" — toolbar + TOC + page stack
  shared/
    a4-page.tsx               ← A4 wrapper (794×1123)
    icon.tsx                  ← Material Icons Outlined span
    certainty-chip.tsx        ← 已確認 / 高可能 / 資料不足 chip
    section-title.tsx         ← SEC num + EN label + title + optional sub
    page-header.tsx           ← running header (section + page num)
    page-footer.tsx           ← brand, "Cortex · Brand Intelligence", page num
    grid-bg.tsx               ← faint 36px grid overlay
    constellation-svg.tsx     ← brand center + product orbit + media nodes SVG
  pages/
    page-1.tsx                ← Cover (constellation centerpiece)
    page-2.tsx                ← 品牌核心 · The Anatomy
    page-3.tsx                ← 產品線結構 · Portfolio
    page-4.tsx                ← 媒體網絡 · The Reachable Galaxy
    page-5.tsx                ← 競品輪廓 · Competitor Landscape
    page-6.tsx                ← 戰略洞察 · Strategic Insights
    page-7.tsx                ← 讀者熱問 + 通路布局
    page-8.tsx                ← 風險 + 來源 + 品質評估
```

## Fonts

Added to `tokens.css` Google Fonts import:
- `Noto Sans TC` — Chinese sans-serif body
- `Noto Serif TC` — Chinese serif pull quotes  
- `Fraunces` — English display serif

New CSS vars:
- `--font-serif` → `"Fraunces", Georgia, serif`
- `--font-serif-tc` → `"Noto Serif TC", "Noto Serif", Georgia, serif`

## Viewer Behaviour

| Feature | Detail |
|---|---|
| Zoom | 55–150% in 5% steps; fit-to-width on resize (55–100% cap) |
| TOC | IntersectionObserver, threshold 0.3/0.5/0.7; active page highlighted lime |
| Print | `window.print()` — `@media print` hides toolbar + TOC, one page per sheet |
| Download PDF | Link to `/v1/brand/{brandId}/report/{reportId}/pdf` (COR-80; may 404) |
| Back | `router.back()` → returns to dashboard |

## Data Fetch (server-side)

`fetchBrandReport(claims, brandId, reportId): Promise<ReportEnvelope>`

- `GET /v1/brand/{brand_id}/report/{report_id}`
- Returns `ReportEnvelope { reportId, status, error?, report? }`
- `report` is the full `BrandIqReport` object when `status == "ready"`

## BrandIqReport TS Type

camelCase, mirrors the BRAND_IQ data.jsx contract exactly. Defined in `cortex-api.ts`.

## Honesty / 資料不足

- `endorsements.status === "資料不足"` → CertaintyChip renders with muted grey tone
- Any empty list renders a CertaintyChip "資料不足" inline — never blank white space
- This is a visual contract, not data-layer logic

## Tests (vitest)

- `report-viewer.test.tsx` — renders all 8 pages from BRAND_IQ fixture; toolbar shows title; TOC has 8 items; zoom +/- updates scale label
- `page-2.test.tsx` — renders core items; renders 資料不足 chip for empty core list
- `page-8.test.tsx` — renders risks; renders 資料不足 sources for empty source list
- Mock IntersectionObserver + ResizeObserver in test setup

## Print CSS

```css
@media print {
  .report-toolbar, .report-toc { display: none !important; }
  .report-page-stack { display: block !important; overflow: visible !important; }
  .report-page-wrapper { page-break-after: always; break-after: page; }
}
```
