# COR-83: Knowledge Base Page

**Date:** 2026-05-24
**Status:** Implementation
**Branch:** `feature/cor-83-knowledge-base`
**Epic:** Brand IQ Report (Slice 5 of N)

## Decision

Replace the placeholder `/knowledge` page with a real server-rendered Knowledge Base that surfaces Brand Reports (via the `listBrandReports` API), version history, and placeholder sections for future KB resources (product knowledge cards, brand voice samples, competitor notes, weekly report).

The Knowledge Base is the permanent "library" entry for everything Cortex synthesises for the brand. It is not a new bounded context — it reads from the existing Brand IQ report list endpoint (COR-81/COR-75 work) and holds forward stubs for features without APIs yet.

## Route

`web/src/app/knowledge/page.tsx` — keep the `/knowledge` path (sidebar already links there).

- Server component
- `auth()` → if no session or `activeContext.kind !== "brand"` → `redirect("/signin")`
- `listBrandReports(claims, brandId)` from `cortex-api.ts`
- Empty list (no reports) → clean empty-state UI
- List present → render `<KnowledgeBasePage versions={...} brandId={...} />`

## `listBrandReports` signature (confirmed from cortex-api.ts)

```ts
listBrandReports(
  claims: CortexTokenClaims,
  brandId: string,
): Promise<ReportVersionItem[]>
```

Where `ReportVersionItem`:
```ts
interface ReportVersionItem {
  reportId: string;
  version: string;
  createdAt: string;
  status: string;       // "current" | "archived"
  current: boolean;
  costUsd?: number | null;
}
```

## Component Breakdown

```
web/src/components/knowledge-base/
  knowledge-base-page.tsx       ← layout orchestrator (tabs, sections)
  featured-report-card.tsx      ← current report highlight card
  version-history-table.tsx     ← all versions, newest-first
  other-resources.tsx           ← pending placeholders (NO invented counts)
```

## Page Layout (prototype: KnowledgeBaseStage, lines 351-519)

1. **Breadcrumb** — BRAND CORTEX (monospace overline, muted)
2. **Title** — "Knowledge Base" (h1, 28px, bold, tight tracking)
3. **Description** — one sentence; uses brand name from first version's report or generic fallback
4. **Tabs** — "Brand Reports" active; "所有檔案" / "產品知識卡" / "Brand Voice 樣本" / "競品筆記" muted + disabled/not-clickable (no API yet)
5. **Featured card** — the CURRENT report (`versions.find(v => v.current)`); mini cover thumbnail, title, badges, buttons
6. **Version history table** — all versions, newest-first (may include current)
7. **Other resources section** — four row stubs: product knowledge cards, brand voice samples, competitor notes, weekly report template — all clearly "準備中" with NO counts
8. **Info panel** — dashed border advisory note

## Featured Report Card

- Mini cover: dark teal gradient thumbnail (88×116px), monogram "B IQ · {version}", brand name
- Badges: "最新" amber pill (current only), version tag (monospace pill), "PDF" pill
- Title: "{version} Brand IQ 報告"
- Generated date from `createdAt`
- Preview button → `/brand/reports/{reportId}` (navigate to report viewer)
- Download PDF button → `/brand/reports/{reportId}/pdf`

## Version History Table

- Grid: version tag | date | status badge | download link
- "現行" green pill for `current === true` (or `status === "current"`)
- "archived" for others (muted)
- Download link → `/brand/reports/{reportId}/pdf`
- No delete/archive actions at MVP

## Other Resources — CRITICAL HONESTY

These four rows are **pending placeholders**. They MUST NOT show invented counts.

| Row | Label | State |
|-----|-------|-------|
| 產品知識卡 | Product Knowledge Cards | 準備中 |
| Brand Voice 樣本 | Brand Voice Samples | 準備中 |
| 競品筆記 | Competitor Notes | 準備中 |
| 週報模板 | Weekly Report Template | 準備中 |

Each shows: icon, label (no count), description explaining what it will contain, "準備中" badge.

## Empty State

When `versions.length === 0`: centred illustration area with message "尚無 Brand IQ 報告" and sub-text explaining that a report is generated after onboarding. No redirect.

## Tests (vitest, jsdom)

File: `web/src/components/knowledge-base/__tests__/knowledge-base-page.test.tsx`

- Renders featured card from fixture with current version
- Preview href → `/brand/reports/{reportId}`
- Download href → `/brand/reports/{reportId}/pdf`
- Version history shows all fixture versions
- "現行" badge on current version
- Other-resources rows are all in "準備中" state (no counts)
- Empty state rendered when versions = []

## Design Tokens Used

- `--mly-teal-*`, `--mly-ink-*`, `--cortex-amber-*` from tokens.css
- `--font-mono`, `--font-sans`, `--font-serif-tc`
- Inline styles (matches report-viewer + prototype pattern; no new CSS files)
