# Cortex Discover v2.0 — Design Spec

**Status:** approved for planning
**Date:** 2026-05-20
**Surface:** Brand Cortex · Discover · route `/brand/dashboard` (kept; spec's `/brand/discover` not adopted)
**Design source of truth:** handoff bundle `Xh5OW2r9ZbZVtrE6EcML3w` →
`cortex/project/handoff/Cortex Discover - Spec.html` (v2.0, 14 sections) plus its
imports: `cortex/project/cortex/{dashboard.jsx,discover.css,cortex-composer.jsx,cortex-composer.css,data.jsx}`,
`cortex/project/handoff/tokens.css`, `cortex/project/design-system-update/colors_and_type.css`,
`cortex/project/handoff/CHANGELOG-v1.2-sidebar.md`. Bundle extracted to `/tmp/cortex-handoff/`
(scratch; **not** committed — `project/` is untracked in this repo).
**Implementation target:** `cortex/web` (Next.js 16, App Router, Tailwind, shadcn/ui).

The reference HTML/JSX is a prototype. We recreate its **visual output** pixel-faithfully
in the existing Next.js architecture; we do not copy its inlined-Babel structure.

---

## 1. Decision log (locked with the user)

| # | Decision | Choice |
|---|---|---|
| 1 | Scope | **Full v2 build** — all 8 stage regions + query layer + docked drawer + ⌘K + data contract |
| 2 | Workflow | brainstorm → **this spec** → `writing-plans` → subagent-driven parallel execution w/ review checkpoints |
| 3 | Route | **Keep `/brand/dashboard`** (spec's `/brand/discover` not adopted; avoids routing/auth/nav churn) |
| 4 | Sidebar | **v2 spec §04 wins** — supersedes the earlier session "Discover-only" trim |
| 5 | Approach | **A — in-place v1.2→v2 delta** (extend `globals.css`/`tokens.css`, rebuild the `.sp` tree, keep shell/route/auth) |
| 6 | Empty state | **Re-skin `EmptyDiscover` to v2 tokens/recipes** (behavior unchanged; loading/error states remain out of scope per spec §14) |
| 7 | Data model | **Plain serializable data + render mapping** — no JSX in the data module; a `RichText` segment model + `<Rich>` renderer |
| 8 | Old code | **Delete superseded v1.2 code** as v2 lands (repo convention: no dead code; recoverable via git) |

Earlier-session note: the "Discover-only" sidebar trim on branch
`worktree-ui-tweak-dashboard` is **superseded** by decision 4/§9 here. The branch is
rebased on `origin/develop@761e001`. Pre-existing upstream `tsc` errors in
`src/app/(auth)/onboarding/{manual/,}page.tsx` (PR #37 typedRoutes) are **not** introduced
by this work and are out of scope.

---

## 2. Architecture & integration

### 2.1 Unchanged

- `src/app/brand/layout.tsx` → `OnboardingGate` (server decision ladder) → `BrandShell`.
- Route `/brand/dashboard`; all referencing call-sites stay valid (root redirect,
  sidebar logo/nav, onboarding-completion redirects, history back-link,
  onboarding-gate retry).
- `mock-session-provider` / `mock-session.ts` / dev-bypass
  (`NEXT_PUBLIC_DEV_BYPASS_AUTH=true`) — unchanged. Demo brand = `CMO / Wang` /
  `Acme Bank Asia` / `enterprise`.

### 2.2 Shell — `src/components/shell/brand-shell.tsx`

`BrandShell` already owns `sidebarOpen` and renders the `.geo-app` grid with
`data-seam="bridge"` + `data-sidebar`. v2 **lifts drawer state here** so the 3rd grid
column, sidebar collapse, and trigger visibility coordinate in one place:

- New state `drawerOpen: boolean` (default `false`).
- `<div className="geo-app" data-seam="bridge" data-sidebar={…} data-drawer-open={drawerOpen ? "true" : undefined}>`.
- Provide drawer open/close + `value`/`model` composer state via context (a
  `DiscoverDrawerProvider`) OR props threaded to the page. **Chosen:** a small React
  context (`useCortexDrawer()`) created in `brand-shell.tsx` so the in-stage query
  strip, the fixed ⌘K trigger, and the docked drawer share one state without prop
  drilling (mirrors the reference's lifted state in `DiscoverDashboard`).
- Global keybinding: `⌘K` / `Ctrl K` toggles the drawer; `Esc` closes it. Bound in
  `BrandShell` (effect with `keydown` listener, cleaned up on unmount). Ignore when
  focus is in an input/textarea except `Esc`.
- The drawer **does not unmount on close** — it animates width/opacity; conversation
  state (input `value`, selected `model`) is preserved.

### 2.3 `.geo-app` grid

Current (keep): `grid-template-columns: 240px minmax(0,1fr)`; collapsed →
`0 minmax(0,1fr)`; `min-width:1320px` (1080 collapsed); transition
`grid-template-columns 280ms var(--ease-std), min-width 280ms var(--ease-std)`.

Add (v2):

```css
.geo-app[data-drawer-open="true"]                       { grid-template-columns: 244px 1fr 420px; }
.geo-app[data-sidebar="closed"][data-drawer-open="true"]{ grid-template-columns: 0 1fr 420px; }
.geo-app[data-drawer-open="true"] .cmp-drawer-backdrop  { display: none; }   /* docked, not modal */
.geo-app[data-drawer-open="true"] .cmp-drawer-trigger   { display: none; }   /* no duplicate */
.geo-app[data-drawer-open="true"] .cmp-drawer           { box-shadow: none; border-left: 1px solid var(--border-soft); }
```

The drawer remains `position:fixed; right:0; width:420px`; the reserved 3rd grid
column prevents content overlap while keeping the slide animation. Stage column is
`1fr` (drops the `minmax(0,1fr)` only in the drawer-open template, matching reference).

**Faithful-port note (not a typo):** the reference uses `240px` for the sidebar in
the base grid but `244px` in the drawer-open template (`244px 1fr 420px`). Keep both
verbatim — do not "normalize" to one value. The `--shell-sidebar-w` token stays
`240px`; the drawer-open template literally uses `244px` as in `discover.css`.

---

## 3. Token & recipe strategy

### 3.1 `src/app/tokens.css`

`tokens.css` is already ~v2 (brand teal, ink, status, cortex amber/purple, sidebar
mist, `--text-*`, `--sp-*`, `--r-*`, `--elev-*`, `--shell-*`, `--grid-*`, `--bp-*`,
`--funnel-*`, `--ease-std`, `--dur-*`). **Gap audit before edits** (verify against the
extracted `handoff/tokens.css` + `design-system-update/colors_and_type.css`):

- `--mly-border-soft` / `--border-soft` (referenced by `discover.css .cq-bar`,
  `.alert`, `.cmp-drawer` docked border). `colors_and_type.css` defines
  `--mly-border-soft: var(--mly-ink-150)` and `--border-soft: var(--mly-border-soft)`.
  Add if absent.
- `--border: var(--mly-ink-200)` alias — confirm present (used by `.sp .chip`).
- `--mly-lime-400: #9CCC65` — present in `colors_and_type.css`, confirm in app tokens.
- Do **not** wholesale-replace `tokens.css`; add only missing variables so nothing
  else in the app shifts. Final file should be a superset matching
  `colors_and_type.css` v2 semantics.

### 3.2 `src/app/globals.css`

Additive v2 deltas. Recipes transcribed verbatim from `cortex/discover.css` +
`cortex/cortex-composer.css` (§7 has the per-region values). Net changes:

- **Add:** `.sp .alerts` + `.sp .alert*`; `.sp .cq*`; `.sp .funnel .flow` grid
  template + `.conn.is-bottleneck`/`.is-leverage` + `.fnl-takeaway`; `.sp .top .left
  .page-title/.crumb/h1/.subtitle`; `.sp .hero .mini .mini-spk`; competitor
  `.h2h.you/.lead` `::before/::after` YOU/LEADER tags + cleaner legend;
  `.geo-app[data-drawer-open]` rules; `@keyframes cqFadeIn`.
- **Replace (v1.2 → v2):** `.sp .top` left side (live-status pill → page-title block);
  `.cmp-drawer-trigger` (top-right 56×56 square → bottom-right 44px "Ask Cortex ⌘K"
  pill); `.sp .funnel .flow` (flex bars → grid blocks+arrows); KPI mini `.bar`
  progress → `.mini-spk` sparkline.
- **Delete (superseded, per decision 8):** `.sp .insight*` (banner → alerts), the
  old top-right FAB rule, old funnel flex-flow rule, KPI mini `.bar` rule.
- `.sp` is the only consumer of these recipes (confirmed by codebase map), so
  replace/delete is safe; still scope every selector under `.sp`/`.geo-app`.

Production attribute values: `data-seam="bridge"`, drawer behavior via
`data-drawer-open`. The Tweaks panel, `data-composer` switching, dock/hero composer
recipes are **not ported** (design-exploration only, spec §14).

---

## 4. Data contract

### 4.1 RichText model (decision 7)

Reference embeds JSX (`<b>…</b>`) in data. We serialize:

```ts
// src/lib/discover/rich-text.ts
export type RichSpan = string | { b: string };
export type RichText = readonly RichSpan[];
// <Rich> renders: string → text node; {b} → <b>{…}</b>
```

`<Rich value={…} />` is a tiny pure component. Conversions (exact, from `data.jsx`):

- `<><b>8 brand answers missing</b> on tracked questions</>` →
  `[{ b: "8 brand answers missing" }, " on tracked questions"]`
- `<><b>Articles</b> · indexed</>` → `[{ b: "Articles" }, " · indexed"]`
- Takeaway → a `RichText` for the sentence; `takeawayCta` is a separate plain string.

### 4.2 Types

```ts
// src/lib/discover/types.ts
export type AlertKind = "warn" | "opp" | "sig";
export interface Alert {
  kind: AlertKind;
  icon: string;          // Material Icons Outlined ligature
  cat: string;           // short caps label, e.g. "GAP" | "WIN" | "WATCH"
  headline: RichText;
  sub: string;
  cta: string;           // includes trailing "→"
}
export interface Hero { v: string; suffix: string; delta: string; note: string; live: string; }
export interface Mini { lab: string; v: string; note: string; trend: "answers"|"views"|"clicks"; }
export interface FunnelBlock { v: string; nm: RichText; here?: boolean; badge?: string; }
export interface FunnelArrow { rate: string; label: RichText; kind?: "bottleneck"|"leverage"; }
export interface Funnel { blocks: FunnelBlock[]; arrows: FunnelArrow[]; takeaway: RichText; takeawayCta: string; }
export interface MediaRow { rk: string; nm: string; badge?: string; vis: number; clk: string; }
export interface CompRow  { nm: string; pct: number; you?: boolean; lead?: boolean; }
export interface DiscoverData {
  alerts: [Alert, Alert, Alert];
  hero: Hero;
  minis: [Mini, Mini, Mini];
  funnel: { blocks: FunnelBlock[]; arrows: FunnelArrow[]; takeaway: RichText; takeawayCta: string };
  media: { sub: string; rows: MediaRow[] };
  comp:  { sub: string; rows: CompRow[]; gap: string };
}
export interface QueryPreset extends DiscoverData { chip: string; }  // chip = "Filter applied" label
export interface QueryChip { id: string; icon: string; label: string; }  // wired iff QUERY_PRESETS[id]
```

### 4.3 Fixtures (`src/lib/discover/mock.ts`, replaces `src/lib/discover-mock.ts`)

Transcribe **verbatim** from `cortex/dashboard.jsx`:

- `BASE_DATA: DiscoverData` — alerts (GAP warn / WIN opp / WATCH sig), hero
  `18.4% ▲ 3.1 pp`, minis (`Brand-cited answers`=94, `Answer views`=4,580,
  `Brand clicks`=284), funnel blocks `320/890/94*/4,580/284` (3rd `here:true`,
  badge `✦ 18.4% visibility`), arrows `×2.8` / `11.0% bottleneck` / `49× leverage` /
  `6.2% CTR`, media 5 rows (鉅亨網 leader…), comp 4 rows (`Your brand` you,
  `Competitor A` lead…), gap `−15.8 pp`.
- `QUERY_PRESETS: { mortgage: QueryPreset; competitor: QueryPreset }` — full
  overrides (no partials), each adds `chip`. Values verbatim from `QUERY_PRESETS`
  in `dashboard.jsx`.
- `QUERY_CHIPS: QueryChip[]` = `[{mortgage,home_work,"Show me mortgage topics"},
  {competitor,compare_arrows,"Compare to Competitor A"},
  {missing,report_problem,"Where am I missing answers?"}]`. `missing` has **no**
  preset → chip rendered disabled (`opacity .5; cursor:not-allowed`, title "Demo
  data not wired for this query yet"). (Spec §14: wire later.)
- `COMPOSER_MODELS` retained for the drawer model picker (Gemini Flash/Pro, Claude
  Opus 4.7, GPT-5, + "Mlytics Cortex AUTO").
- The KPI bug-fix is already in the reference values (mini 1 = `Brand-cited
  answers`=94, not 284). No extra work — just transcribe correctly.

All old `discover-mock.ts` exports removed; update/remove the only consumers
(Discover page + `EmptyDiscover` if it imports any) per decision 8.

---

## 5. Component tree & file map

`src/components/brand-dashboard/discover/` (rebuilt):

| File | Action | Responsibility |
|---|---|---|
| `discover-dashboard.tsx` | create | `"use client"`. Owns `activeQuery` state; `data = activeQuery ? QUERY_PRESETS[activeQuery] : BASE_DATA`. Renders `.pg.sp` stage with all regions. Reads `useCortexDrawer()` for the trigger/drawer. |
| `topbar.tsx` | create | `.sp .top` — page-title block (crumb/H1/subtitle+muted) + filter chips + Export. |
| `priority-alerts.tsx` | create | `.sp .alerts`, 3 `.alert.is-{kind}`; keyed `alerts-${activeQuery||"base"}` for remount + `cqFadeIn`. |
| `cortex-query-strip.tsx` | create | `.sp .cq` — bar (mark/input/version) + `.cq-suggest` chips ↔ `.cq-applied` chip; calls `onQuery/onClear`. |
| `kpi-row.tsx` | create | `.sp .hero` grid `1.4fr 1fr 1fr 1fr`; `h-main` + 3 `mini`; keyed on `activeQuery` for `cqFadeIn`. |
| `hero-sparkline.tsx` | create | SVG 480×180, stroke `#1C726B` 2px, area gradient `0.18→0`. |
| `mini-sparkline.tsx` | create | SVG 140×28, stroke `#1C726B` 1.5px round caps, 0.9 opacity; `trend` selects point set. |
| `geo-funnel.tsx` | create | `.sp .funnel` — `.flow` grid 5 blocks + 4 `FunnelArrow`; `.is-here`; `.fnl-takeaway`. |
| `funnel-arrow.tsx` | create | `.conn` + `.is-bottleneck`/`.is-leverage`; SVG arrow line. |
| `media-competitor-grid.tsx` | create | `.sp .grid` (1.45fr/1fr): media table + competitor h2h + legend. |
| `cortex-drawer.tsx` | create | `.cmp-drawer` docked panel: head, empty state (icon/title/sub/4 quick), foot `ComposerCard` + disclaimer. Portaled; rendered when drawer mode active, visible per `drawerOpen`. |
| `ask-cortex-trigger.tsx` | create | `.cmp-drawer-trigger` fixed bottom-right pill (CortexMark + "Ask Cortex" + `⌘K`). Hidden when drawer open. |
| `composer-card.tsx` | create | shared input + foot (ModelPill, add, version, mic, send) used in drawer foot. |
| `model-picker.tsx` | port | `.mdl-pill` + portaled `.mdl-pop` (Auto + 4 models). |
| `cortex-mark.tsx` | keep | SVG brand mark (already in repo). |
| `empty-discover.tsx` | modify | re-skin to v2 tokens/recipes; behavior/logic unchanged (decision 6). |
| `sections.tsx`, v1.2 `cortex-composer.tsx`, `cortex-prompt.tsx`, unused `kpi-card.tsx`/`funnel-card.tsx`/`time-range-filter.tsx`/`publisher-breakdown-table.tsx` | delete if unreferenced after swap | per decision 8; verify no other importers first |

Other:

- `src/app/brand/dashboard/page.tsx` — modify: render `<DiscoverDashboard/>`
  (gate populated vs `EmptyDiscover` on `connectedSourceCount===0 && !demo` exactly
  as today).
- `src/components/shell/brand-shell.tsx` — modify: drawer state/context, `⌘K`/`Esc`,
  `data-drawer-open`, render `<AskCortexTrigger/>` + `<CortexDrawer/>` at shell level.
- `src/components/shell/sidebar.tsx` — modify per §9.
- `src/app/tokens.css`, `src/app/globals.css` — modify per §3.
- `src/lib/discover-mock.ts` → replaced by `src/lib/discover/{types,rich-text,mock}.ts`.

---

## 6. Region pixel specs (transcribed from reference)

> All values verbatim from `cortex/discover.css` / `cortex/cortex-composer.css` /
> `dashboard.jsx`. Frame baseline **1440×1180**, content ~1180, sidebar 240–244.
> Fonts: `--font-sans` Noto Sans, `--font-numeric` Roboto, `--font-mono` Roboto Mono.

### 6.1 Stage shell
`.pg{min-height:100vh;padding:24px 32px 48px;background:#F4F2EA;overflow-y:auto}`.
`.sp .top{display:flex;justify-content:space-between;gap:24px;position:sticky;top:0;z-index:20;background:transparent;padding:12px 32px;margin:-24px -32px 20px}`.
`.sp .card{background:#fff;border:1px solid #E6E1D2;border-radius:10px;padding:22px;box-shadow:0 1px 0 rgba(160,140,90,.06),0 2px 8px rgba(60,42,12,.04)}`.
Section vertical rhythm: each block `margin-bottom:14px`.

### 6.2 Topbar (§05)
Left `.page-title`: `.crumb` `700 10.5px var(--font-mono)` teal-700 uppercase
`letter-spacing:.12em` `margin-bottom:4px` text `BRAND CORTEX`; `h1`
`700 26px/1.2 var(--font-sans)` `-0.012em` ink-900; `.subtitle`
`400 13px/1.5` ink-700, `.muted` ink-500 `var(--font-mono) 11.5px` (freshness ts).
Right: `.chip` (h32, `#fff`, `1px var(--border)`, `r6`, `500 13px`, ink-700, icon
15px ink-500), `.chip.is-on` (teal-050 fill, teal-400 border, teal-700 600);
`.btn` Export (h32, teal-700 fill, white, r6, `600 13px`, `file_download` 15px;
hover teal-800).

### 6.3 Priority alerts (§06, NEW)
`.sp .alerts{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:14px;animation:cqFadeIn 280ms var(--ease-std)}`.
`.alert{background:#fff;border:1px solid var(--border-soft);border-radius:10px;padding:18px 20px 16px;display:flex;flex-direction:column;gap:6px}`.
`.alert-head{display:flex;align-items:center;gap:8px;margin-bottom:4px}` icon 16px;
color by kind: warn `var(--mly-warn-strong)`, opp `var(--mly-teal-700)`, sig
`var(--mly-ink-500)`. `.alert-cat` `700 9px` caps `.06em` `2px 6px` `r3` —
warn `#FBEFD8/#8A4E11`, opp `#EAF5F2/teal-700`, sig `ink-100/ink-600`.
`.alert-body` `400 13.5px/1.5` ink-800, `<b>` ink-900 700. `.alert-sub`
`400 11.5px/1.5` ink-500. `.alert-cta` text-only `600 12.5px` teal-700,
`align-self:flex-start;margin-top:8px`, hover teal-800 + underline.
Rule: exactly 3 (pad with WATCH before showing fewer).

### 6.4 Cortex query strip (§07, NEW)
`.cq` `margin-bottom:14px`. `.cq-bar` `display:flex;gap:12px;padding:10px 14px 10px 12px;background:#fff;border:1px solid var(--border-soft);border-radius:10px;box-shadow:0 1px 2px rgba(0,0,0,.04)`;
`:focus-within` teal-400 border + `0 0 0 3px rgba(56,166,154,.12)`.
`.cq-mark` 32×32 `linear-gradient(135deg,teal-700,teal-900)` white, `r8`,
`auto_awesome` 18px. `.cq-input` flex `400 14px`, placeholder ink-400 — text
`"Ask Cortex — your dashboard will answer in place"` (idle) /
`"Refine the answer…"` (active). `.cq-version` `400 11px var(--font-mono)`
ink-400 = `"Cortex v3.2 · grounded in 320 articles"`.
Default: `.cq-suggest` (label `"Try"` `500 11px` caps + `.cq-chip` pills:
`6px 12px 6px 10px`, `1px var(--border-soft)`, `r999`, `500 12.5px`, ink-700,
hover teal-050/teal-400/teal-700; `:disabled` `.5`/not-allowed).
Active: `.cq-applied` (`linear-gradient(90deg,rgba(56,166,154,.14),rgba(56,166,154,.02))`,
`1px var(--mly-teal-200)`, `r999`, `5px 6px 5px 12px`) with `filter_alt` icon,
`.cq-applied-lbl` `"Filter applied:"` `11px 600` caps teal-700,
`.cq-applied-val` `12.5px 600` ink-900 (= preset `chip`), `.cq-clear` 22×22 round
`close`, clears state.

### 6.5 KPI row (§08)
`.sp .hero{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:14px;margin-bottom:14px;animation:cqFadeIn 280ms var(--ease-std)}` (keyed on `activeQuery`).
`.h-main`: gradient `linear-gradient(180deg,#fff 0,#fff 60%,#FBF9F1 100%)`,
`1px #E6E1D2`, `overflow:hidden;position:relative`. `.lab` `700 10.5px` caps
`.12em` ink-500 + `.live` (`500 10.5px var(--font-mono)` teal-700, dot 6px teal-700
`0 0 0 3px rgba(28,114,107,.15)`). `.v` `700 88px/1 var(--font-numeric)`
`-0.035em` ink-900; `sup` `700 36px` ink-400 weight 500. `.sub` row: `.up`
(teal-700 700, `#EAF5F2` pill `3px 8px` `r999` `12.5px`) + note ink-600
`500 13px`. `.spk` absolute `right:-1px;bottom:-1px;width:54%;opacity:.9`.
`.mini`: col flex; `.lab` like hero; `.v` `700 38px/1.05` `-0.02em` ink-900
`margin-top:8px`; `.row b` `500 12px var(--font-mono)` teal-700 600; `.mini-spk`
block `width:100%;height:28px;margin-top:4px;opacity:.9`.

### 6.6 GEO funnel (§09)
`.sp .funnel{padding:22px 24px 24px;background:#fff;border:1px solid #E6E1D2;border-radius:10px;margin-bottom:14px;box-shadow:…}`.
`.fh h3` `700 15px` ink-900 + `small` `400 12px` ink-500 (`Article → click —
last 30 days`). `.flow{display:grid;grid-template-columns:1fr auto 1fr auto 1.1fr
auto 1fr auto 1fr;align-items:end;gap:0 14px;padding-top:8px}` (5 `.blk` + 4
`.conn` interleaved). `.blk{display:flex;flex-direction:column;align-items:flex-start;
padding:14px 16px;border-radius:8px;background:#FAF7EE;border:1px solid #ECE5D2;
min-height:106px;justify-content:space-between}`; `.blk .v` `700 30px/1
var(--font-numeric)` `-0.018em` ink-900; `.blk .nm` `500 12px` ink-700
(`<b>` ink-900). `.blk.is-here` `linear-gradient(180deg,#F2F8F5,#EAF2EC)`,
`1px var(--mly-teal-200)`, `0 0 0 3px rgba(28,114,107,.06)`; nm → teal-700;
`.badge` `600 10.5px` teal-700 white bg `1px teal-200` `2px 7px` `r999`.
`.conn{display:flex;flex-direction:column;align-items:center;gap:4px;padding-bottom:22px}`;
`.r` `600 12px var(--font-mono)` ink-800; `.l` `400 10.5px var(--font-mono)`
ink-400 `.04em` uppercase; SVG arrow line `#9E9E9E`.
`.conn.is-bottleneck .r` `#FDEAEA` / `var(--mly-danger)` `2px 9px` `r999`
`0 0 0 2px rgba(229,57,53,.08)` 700; `.l b` danger `9.5px` caps.
`.conn.is-leverage .r` `#DCF3E7` / `#1E7A4C` `2px 9px` `r999`
`0 0 0 2px rgba(38,166,154,.12)` 700; `.l b` `#1E7A4C` `9.5px` caps.
`.fnl-takeaway{margin-top:16px;padding:12px 16px;background:#FFFBEF;border:1px
solid var(--mly-warn);border-radius:6px;display:flex;align-items:center;gap:10px;
font:400 13px/1.55}` ink-900, `lightbulb` 18px `var(--mly-warn-strong)`, `<b>`
ink-900 700, trailing `a` (teal-700 `600 12.5px`, `margin-left:auto`, hover
underline) = `takeawayCta`.

### 6.7 Bottom grid (§10)
`.sp .grid{display:grid;grid-template-columns:1.45fr 1fr;gap:14px}`.
Media `.row` grid `22px 1.4fr 2fr 50px 50px` gap 14, `border-top:1px solid
#E9E2D0`, `13.5px`; `.row.head` `700 10.5px` caps ink-500 border-bottom
`#D7D0BC`; `.rk` `700 11.5px var(--font-numeric)` ink-400; `.nm` 600 ink-900 +
`.badge` (`600 9px` `.06em` `#EAF5F2`/teal-700 `2px 5px` `r3` uppercase; preset
queries override text e.g. `rising`, `−12 pp`); `.bar i` h8 `r4`
`linear-gradient(90deg,teal-700,teal-400)` width `vis*2.4%`; `.pct`
`600 13px var(--font-numeric)` ink-900 right; `.clk` `500 12.5px var(--font-mono)`
ink-500 right. Header link `View all 32 →` teal-700 `500 12.5px`.
Competitor `.h2h` grid `96px 1fr` gap12, `border-top #E9E2D0` (first `#D7D0BC`);
`.nm` `500 12.5px` ink-700; `.h2h.you .nm` ink-900 700; `.track` h24
`#F4EFDF` `r4` `1px #E6E1D2`; `i` absolute fill width `pct*2.4%`
(default ink-400; `.you` `linear-gradient(90deg,teal-700,teal-500)`;
`.lead` `linear-gradient(90deg,warn-strong,warn)`); `.lbl` `700 12px
var(--font-numeric)` (right ink-900; `.you` white left). YOU/LEADER tags via
`.h2h.you .nm::before{content:"YOU";…teal-700/#fff}` /
`.h2h.lead .nm::after{content:"LEADER";…var(--mly-warn)/#6B4500}` (`700 9px`
`.06em` `2px 5px` `r3`, stacked above name, `order:-1`). `.legend`
`400 12.5px` ink-700, `trending_down` 16px danger + `"Gap to leader"` +
`<b>` danger 700 `var(--font-numeric)` tabular = `comp.gap`.

### 6.8 Docked drawer (§11, NEW behavior)
`.cmp-drawer{position:fixed;top:0;right:0;bottom:0;width:420px;z-index:80;
background:#FAF8F1;border-left:1px solid #E6E1D2;display:flex;flex-direction:
column;animation:cmp-slide-in 260ms var(--ease-std)}`. Docked overrides in §2.3
(no shadow, border-left, no backdrop, reserved grid col). Internals:
`.head` `16px 18px 14px` border-bottom ink-150, `.title` `700 15px` ink-900,
`.close` 30×30 round (`close` 18px). `.empty` centered col gap16:
`.hero-ic` 64×64 `r16` `linear-gradient(135deg,teal-700,teal-400)` white
`auto_awesome` 32px shadow `0 10px 28px rgba(28,114,107,.32)`; `.hero-title`
`700 20px` ink-900; `.hero-sub` `400 13px/1.5` ink-500 `max-width:280px`;
`.quick` 2-col grid gap8 of pill buttons (`#fff` `1px ink-150` `r999`
`500 12.5px`; hover teal-050/teal-200/teal-700) — labels from `DRAWER_QUICK`.
`.foot` border-top ink-150 bg `#FAF8F1`: `ComposerCard` (`--cmp-radius:12px;
box-shadow:none`, input `14px 16px 6px` 14px) + `.disclaimer`
`400 11px` ink-400 center.
`ComposerCard` `.cmp`: `#fff` `1px #E6E1D2` `r14` shadow; `.cmp-input`
`20px 22px 8px` `400 16px`; `.cmp-foot` `8px 12px 12px` gap8: `ModelPill`
(`.mdl-pill` `r999`, `.mdl-ic` 22×22 teal gradient, `AUTO` tag, chevron),
`.cmp-plus`/`.cmp-mic` 34px round, `.cmp-version` `11px mono` ink-400,
`.cmp-send` (teal-700, white, `r10`, `600 13px`, `arrow_upward`).
`.mdl-pop` portaled fixed `width:400px` `#FAF8F1` `1px #E6E1D2` `r12`
shadow, `mdl-pop-in 180ms`; `Adaptive Routing · Recommended` header;
`.mdl-auto` (Mlytics Cortex AUTO, `#ECE9DB`); `Force direct model` section +
4 `.mdl-row` (icon/title/desc/latency, `data-selected`).

### 6.9 ⌘K trigger (§12, NEW)
`.cmp-drawer-trigger{position:fixed;bottom:24px;right:24px;z-index:100;
display:inline-flex;align-items:center;gap:8px;height:44px;padding:0 16px 0 12px;
background:var(--mly-teal-800);color:#fff;border:none;border-radius:999px;
font:600 13px var(--font-sans);box-shadow:0 8px 24px rgba(20,73,72,.32),0 0 0 1px
rgba(56,166,154,.18);transition:transform 160ms var(--ease-std),box-shadow 200ms}`.
`::after{content:"⌘K";font:500 10.5px "Roboto Mono",monospace;background:rgba(255,
255,255,.14);color:rgba(255,255,255,.88);padding:2px 6px;border-radius:4px;
margin-left:2px}` — render `Ctrl K` on non-Mac. `CortexMark` 24px +
`"Ask Cortex"`. Hover `translateY(-2px)` + denser shadow. Hidden when
`data-drawer-open` (§2.3).

---

## 7. Interaction specs

1. **Query swap (§07).** `.cq-chip` click / ⏎ matching a preset → `activeQuery = id`
   → `data = QUERY_PRESETS[id]`. `.sp .alerts` keyed `alerts-${id||"base"}` and
   `.sp .hero` keyed `${id||"base"}` so React remounts them → `cqFadeIn` 280ms.
   Suggestions row is replaced by `.cq-applied` (preset `chip` + clear). `.cq-clear`
   → `activeQuery=null` → BASE_DATA. Full overrides only (no partial merge).
2. **Drawer dock.** Open via ⌘K, the bottom-right pill, or (future) a CTA. Sets
   `drawerOpen=true` → `.geo-app[data-drawer-open="true"]` → grid grows 420px col
   (280ms), drawer slide-in, trigger hidden, no backdrop. Close via header `close`,
   `Esc`, or `⌘K` toggle. Drawer stays mounted (state preserved).
3. **Sidebar collapse coordination.** Existing chevron/reveal unchanged. Combined
   states: `[data-sidebar="closed"][data-drawer-open="true"]` → `0 1fr 420px`.
4. **Keyboard.** Global `⌘K`/`Ctrl K` toggle, `Esc` close — bound in `BrandShell`;
   suppressed when typing in inputs except `Esc`.

---

## 8. Out of scope (spec §14)

Real Cortex backend behind the query layer (presets only); 3rd "missing" chip
(disabled until backend); loading/error states; mobile <1024 breakpoint (KPI 4→2,
alerts 3→1) — desktop 1180 baseline only; drawer real conversation thread (empty
state only); Tweaks panel + `data-composer` switching + dock/hero composer +
"Speak"/TTS; sidebar-collapse persistence to user prefs. `EmptyDiscover` is
re-skinned (decision 6) but its loading/error variants are **not** added.

---

## 9. Sidebar §04 rework (supersedes earlier trim)

`src/components/shell/sidebar.tsx`, contents per spec §04 (Aurora Mist recipe
unchanged — already canonical in `globals.css .sb`):

- **Keep/restore:** logo; nav (ungrouped top) `Discover` (active, `grid_view`,
  `/brand/dashboard`, `isDefault`) + `History` (`schedule`, `/brand/history`);
  section label `Network` → `Media Network` (`hub`); section label `Agent` →
  `Knowledge Base` (`menu_book`), `Brand Voice` (`campaign`), `Connectors`
  (`cable`); user footer (avatar/name/org/gear).
- **Remove (v2):** "New decision" CTA, `GEO Monitor`, `MONITOR` section label,
  `CONTENT` section (Answer Engine, Answer Site), **Brand Cortex status pod**,
  Enterprise pill. (The earlier-session trim had kept the pod and dropped
  History/Media Network/KB/Brand Voice/Connectors — both are corrected here.)
- Capability gating: keep `requires` filter pattern (`hasCapability`). KB had a
  `view_kb_enterprise`/ENT pill in pre-trim code — v2 removes the Enterprise pill;
  keep KB's capability gate, drop the pill rendering. `SidebarProps` unchanged
  (no consumer churn). Doc-comment updated to the v2 IA.

---

## 10. Decomposition for subagent execution

**Phase 0 — Foundation (serial; one PR/worktree; gates the rest):**
- F1 token/recipe deltas: `tokens.css` gap fills + `globals.css` v2 add/replace/delete (§3).
- F2 data layer: `discover/{types,rich-text,mock}.ts` + `<Rich>`; delete `discover-mock.ts`; fix consumers (§4).
- F3 `BrandShell` drawer context + `⌘K`/`Esc` + `data-drawer-open` + 3-col grid (§2.2–2.3).
- F4 sidebar §04 rework (§9).

**Phase 1 — Regions (parallel subagents after Phase 0):**
- R1 topbar + priority alerts (§6.2–6.3)
- R2 query strip + `activeQuery` wiring + keyed remount/`cqFadeIn` (§6.4, §7.1)
- R3 KPI row + hero/mini sparklines (§6.5)
- R4 GEO funnel + arrows + takeaway (§6.6)
- R5 media + competitor grid (§6.7)
- R6 docked drawer + ⌘K trigger + ComposerCard + model picker (§6.8–6.9, §7.2)
- R7 `EmptyDiscover` v2 re-skin (decision 6)

**Phase 2 — Integration:** assemble `discover-dashboard.tsx`; wire
`page.tsx` populated/empty gate; delete superseded v1.2 files (decision 8);
tests + verification (§11).

Each phase/task: `npm run lint` + `type-check` + `test` green; subagent review per
the user's established model (worktree-parallel, sub-agent review, tech-lead
oversight). Dependencies: Phase 1 ⟂ tasks all depend on Phase 0; R2 depends on
R1+R3+R4+R5 data presence only at integration (Phase 2), not during build (mock
contract is fixed in F2).

---

## 11. Testing & verification

- **Unit/component (vitest + RTL):** `<Rich>` renders strings + bold; alerts render
  3 cards w/ kind classes & icons; query strip toggles suggest↔applied and calls
  `onQuery/onClear`; query swap changes hero/alerts content + remounts (key);
  funnel marks exactly one `.is-here`, bottleneck/leverage classes; competitor
  YOU/LEADER tags; drawer open/close + dock attribute; ⌘K/Esc handler; sidebar §04
  renders the correct items and **not** the removed ones.
- **Suite gate:** full `npm run lint` + `npm run type-check` + `npm test` green.
  The 2 pre-existing upstream `tsc` errors (onboarding routes, PR #37) are tracked
  as out-of-scope and must not increase.
- **Visual (Playwright, dev-bypass `NEXT_PUBLIC_DEV_BYPASS_AUTH=true`):** at
  1440-wide, accessibility snapshot + screenshot per region; verify against the
  reference description (numbers/colors/layout) — do **not** rely on rendering the
  prototype HTML (per bundle README).

### Acceptance checklist
- [ ] Sidebar matches §04 exactly (items present/removed; no status pod; Aurora Mist intact).
- [ ] Topbar = crumb/H1/subtitle + chips + Export (no live-status pill).
- [ ] 3 priority alerts, intent-coded, swap with the query.
- [ ] Query strip swaps alerts+hero in place with `cqFadeIn`; `.cq-applied` + clear restore BASE_DATA; `missing` chip disabled.
- [ ] KPI: hero 88px value + sparkline; 3 minis with sparklines; mini-1 = "Brand-cited answers" 94.
- [ ] Funnel: 5 blocks + 4 arrows grid; one `.is-here` w/ badge; bottleneck (red) + leverage (green) pills; cream takeaway + CTA.
- [ ] Media/competitor grid: badges, YOU/LEADER stacked tags, gap legend.
- [ ] Drawer is **docked** (3rd 420px col, no backdrop/scrim, trigger hidden, border-left); state preserved on close.
- [ ] ⌘K pill bottom-right; `⌘K`/`Ctrl K` toggle, `Esc` close.
- [ ] `EmptyDiscover` re-skinned to v2 tokens; 0-source/!demo gate still works.
- [ ] Old v1.2 Discover code deleted; no dead imports; lint/type-check/test green.

---

## 12. Risks & open items

- **globals.css surgery** (≈1400 lines, shared): mitigate by scoping every selector
  under `.sp`/`.geo-app`, additive-first, delete only confirmed-unreferenced v1.2
  rules. `.sp` is Discover-only per the codebase map.
- **Spec §02 vs §14 tension** (HeroComposer): resolved — production v2 stage has
  **no** in-stage hero composer; the query strip is the in-stage surface; chat lives
  only in the docked drawer + ⌘K trigger. Tweaks/dock/hero not ported.
- **Reference open questions** (handoff README): CDN/brand hexes, KB enterprise gate,
  Speak/TTS, live-decisions WS — all out of scope here; flag to design if they block.
- **Upstream `tsc` errors** (PR #37 onboarding routes) pre-exist on `develop`; not
  this work's responsibility; keep the count from increasing.
- Bundle `project/` stays uncommitted (untracked in this repo); spec references the
  extracted scratch path only.
