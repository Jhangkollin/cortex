# Cortex Discover v2.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `/brand/dashboard` as Cortex Discover v2.0 — 8 stage regions, a Cortex query layer that re-shapes the dashboard in place, a docked Cortex drawer, and a ⌘K trigger — as an in-place v1.2→v2 delta on the existing shell/route/auth.

**Architecture:** Keep `app/brand/layout.tsx → OnboardingGate → BrandShell` and route `/brand/dashboard`. Lift drawer state into `BrandShell` (3rd `.geo-app` grid column + ⌘K/Esc). Replace the `.sp` component tree under `src/components/brand-dashboard/discover/`. Swap `discover-mock.ts` for a serializable `DiscoverData` contract (`RichText` + `BASE_DATA`/`QUERY_PRESETS`). Extend `tokens.css`/`globals.css` with additive v2 deltas; delete superseded v1.2 code.

**Tech Stack:** Next.js 16 (App Router, "use client"), React 19, TypeScript (strict), Tailwind + `globals.css` `.sp`/`.geo-app` recipe vocabulary, CSS custom-property tokens, vitest + @testing-library/react, Playwright (dev-bypass) for visual checks.

**Spec:** `docs/superpowers/specs/2026-05-20-cortex-discover-v2-design.md` (committed `4c49306`). Section refs below (e.g. "spec §6.3") point there. Verbatim CSS/data source: extracted bundle at `/tmp/cortex-handoff/cortex/project/` (`cortex/discover.css`, `cortex/cortex-composer.css`, `cortex/dashboard.jsx`, `cortex/cortex-composer.jsx`). If `/tmp/cortex-handoff/` is gone, re-extract: `tar -xzf <webfetch .bin> -C /tmp/cortex-handoff` (the gzip from the handoff URL).

**Conventions for every task:**
- Run from `web/`. Verify gate = `npm run lint && npm run type-check && npm test`.
- The 2 pre-existing upstream `tsc` errors in `src/app/(auth)/onboarding/{manual/,}page.tsx` (PR #37 typedRoutes) are **out of scope**; `type-check` is "green" iff the error set does **not grow** beyond those 2. Capture the baseline once (Task 0).
- Commits: conventional, scoped `feat(discover):` / `refactor(discover):` / `style(discover):` / `test(discover):`, ending with the `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` trailer. Stage files by explicit path (never `git add -A`). Do not commit `.env.local`, `.playwright-mcp/`, `sidebar-discover-only.png`.
- CSS is the deliverable for style tasks: there is no unit assertion for pixels — verification = `lint`/`type-check`/`build` green + a Playwright visual check at 1440-wide via `NEXT_PUBLIC_DEV_BYPASS_AUTH=true` (seed localStorage `cortex.mock-session.v1` if needed; the dev bypass auto-seeds the demo brand). Component **behavior** is unit-tested with vitest+RTL.

---

## File Structure

**Create**
- `web/src/lib/discover/rich-text.tsx` — `RichText` type + `<Rich>` renderer.
- `web/src/lib/discover/types.ts` — `DiscoverData` and member interfaces.
- `web/src/lib/discover/mock.ts` — `BASE_DATA`, `QUERY_PRESETS`, `QUERY_CHIPS`, `COMPOSER_MODELS`.
- `web/src/components/brand-dashboard/discover/discover-dashboard.tsx` — stage root, owns `activeQuery`.
- `.../discover/topbar.tsx`, `priority-alerts.tsx`, `cortex-query-strip.tsx`, `kpi-row.tsx`, `hero-sparkline.tsx`, `mini-sparkline.tsx`, `geo-funnel.tsx`, `funnel-arrow.tsx`, `media-competitor-grid.tsx`, `cortex-drawer.tsx`, `ask-cortex-trigger.tsx`, `composer-card.tsx`, `model-picker.tsx`.
- Tests colocated under `web/src/components/brand-dashboard/discover/__tests__/` and `web/src/lib/discover/__tests__/`.

**Modify**
- `web/src/app/tokens.css` (gap fills) · `web/src/app/globals.css` (v2 recipe deltas).
- `web/src/components/shell/brand-shell.tsx` (drawer context, ⌘K/Esc, `data-drawer-open`, mount trigger+drawer).
- `web/src/components/shell/sidebar.tsx` (§04 rework).
- `web/src/app/brand/dashboard/page.tsx` (render `<DiscoverDashboard/>`; keep empty gate).
- `web/src/components/brand-dashboard/empty-discover.tsx` (v2 re-skin).

**Delete (Phase 2, after consumers migrated)**
- `web/src/lib/discover-mock.ts`; `web/src/components/brand-dashboard/discover/sections.tsx`; the v1.2 `web/src/components/brand-dashboard/discover/cortex-composer.tsx`; `cortex-prompt.tsx`; and any of `kpi-card.tsx`/`funnel-card.tsx`/`time-range-filter.tsx`/`publisher-breakdown-table.tsx` confirmed unreferenced (`git grep` first).

---

## Task 0: Baseline & branch sanity

**Files:** none (verification only).

- [ ] **Step 1: Confirm branch + clean-ish tree**

Run: `git status --short && git log --oneline -1`
Expected: HEAD is the spec commit (`docs(discover): Cortex Discover v2.0 design spec`); only `web/src/components/shell/sidebar.tsx` modified (the superseded trim — Task F4 overwrites it), plus untracked `.playwright-mcp/` / `sidebar-discover-only.png` (never staged).

- [ ] **Step 2: Capture the type-check baseline**

Run: `cd web && npm run type-check 2>&1 | grep -c "error TS" || true`
Expected: `2` (the known upstream onboarding-route errors). Record the exact 2 lines:
Run: `npm run type-check 2>&1 | grep "error TS"`
Expected exactly:
```
src/app/(auth)/onboarding/manual/page.tsx(58,17): error TS2345: ...
src/app/(auth)/onboarding/page.tsx(57,11): error TS2322: ...
```
"type-check green" for the rest of this plan = this set does not grow.

- [ ] **Step 3: Baseline test suite**

Run: `npm test 2>&1 | tail -3`
Expected: all files passing (record the count, e.g. `Tests 74 passed`).

No commit (no changes).

---

# PHASE 0 — Foundation (serial; gates Phase 1)

## Task F1: Token & recipe deltas

**Files:**
- Modify: `web/src/app/tokens.css`
- Modify: `web/src/app/globals.css`

- [ ] **Step 1: Token gap audit**

Run: `cd web && grep -nE -- '--border-soft|--mly-border-soft|--mly-lime-400|--border:' src/app/tokens.css || true`
Compare against `/tmp/cortex-handoff/cortex/project/design-system-update/colors_and_type.css` (the v2 superset). For each missing variable, add it inside `:root{}` in `tokens.css`:

```css
/* add only if absent — keep existing values untouched */
--mly-border:      var(--mly-ink-200);
--mly-border-soft: var(--mly-ink-150);
--border:          var(--mly-border);
--border-soft:     var(--mly-border-soft);
--mly-lime-400:    #9CCC65;
```

- [ ] **Step 2: Add the new v2 recipes to `globals.css`**

Append a clearly-commented block `/* === Cortex Discover v2 === */`. Transcribe **verbatim**, every selector scoped under `.sp`/`.geo-app`, from `/tmp/cortex-handoff/cortex/project/cortex/discover.css`:
- `.sp .top .left .page-title/.crumb/h1/.subtitle/.subtitle .muted` (discover.css lines ~951–974) — **replaces** the v1.2 live-status left side.
- `.sp .cq*` (query strip, lines ~1130–1262 incl. `@keyframes cqFadeIn`).
- `.sp .alerts` + `.sp .alert*` (lines ~1271–1337).
- `.sp .funnel .flow` grid template + `.blk`/`.blk.is-here`/`.conn` (lines ~629–696) and v2 `.conn.is-bottleneck`/`.is-leverage` + `.fnl-takeaway` (lines ~1021–1066).
- `.sp .hero .mini .mini-spk` (lines ~1010–1019) and competitor `.h2h.you/.lead` `::before/::after` + cleaner legend (lines ~1068–1124).
- Drawer-open grid + dock + bottom-right trigger pill (lines ~1340–1368) and from `/tmp/cortex-handoff/cortex/project/cortex/cortex-composer.css`: `.cmp`, `.cmp-*`, `.mdl-*`, `.cmp-drawer*`, `.cmp-drawer-trigger` (verbatim; trigger is the **bottom-right pill** lines ~292–333, not the old top-right square).

Use spec §6.1–6.9 as the cross-check for exact values.

- [ ] **Step 3: Delete superseded v1.2 recipes from `globals.css`**

Remove: `.sp .insight*` (banner), the old top-right `.cmp-drawer-trigger` square rule, the old `.sp .funnel .flow{display:flex;height:280px…}` rule, the KPI mini `.sp .hero .mini .bar*` progress-bar rules. Replace `.sp .top` left-side rules with the page-title block from Step 2. (Confirm no non-`.sp` consumer: `grep -n 'insight\|cmp-drawer-trigger' src/app/globals.css` and `git grep -n "className=\"[^\"]*insight"` — Discover is the only consumer per spec §3.2.)

- [ ] **Step 4: Verify build + no token regressions**

Run: `npm run lint && npm run type-check 2>&1 | grep -c "error TS"`
Expected: lint clean; error count == baseline (2).
Run: `npm run build 2>&1 | tail -3`
Expected: build succeeds (CSS parses).

- [ ] **Step 5: Commit**

```bash
git add src/app/tokens.css src/app/globals.css
git commit -m "$(cat <<'EOF'
style(discover): v2 token gap-fills + globals.css recipe deltas

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

## Task F2: Data layer (`DiscoverData` contract)

**Files:**
- Create: `web/src/lib/discover/rich-text.tsx`
- Create: `web/src/lib/discover/types.ts`
- Create: `web/src/lib/discover/mock.ts`
- Test: `web/src/lib/discover/__tests__/rich-text.test.tsx`, `web/src/lib/discover/__tests__/mock.test.ts`

- [ ] **Step 1: Write the failing `<Rich>` test**

`web/src/lib/discover/__tests__/rich-text.test.tsx`:
```tsx
import { render, screen } from "@testing-library/react";
import { Rich } from "../rich-text";

test("renders plain strings and bold runs", () => {
  const { container } = render(
    <Rich value={[{ b: "8 missing" }, " on tracked questions"]} />,
  );
  expect(container.textContent).toBe("8 missing on tracked questions");
  expect(screen.getByText("8 missing").tagName).toBe("B");
});

test("renders an all-plain value with no <b>", () => {
  const { container } = render(<Rich value={["per article"]} />);
  expect(container.querySelector("b")).toBeNull();
  expect(container.textContent).toBe("per article");
});
```

- [ ] **Step 2: Run it — expect fail**

Run: `npm test -- rich-text 2>&1 | tail -5`
Expected: FAIL (`Cannot find module '../rich-text'`).

- [ ] **Step 3: Implement `rich-text.tsx`**

```tsx
import { Fragment, type ReactElement } from "react";

export type RichSpan = string | { b: string };
export type RichText = readonly RichSpan[];

export function Rich({ value }: { value: RichText }): ReactElement {
  return (
    <>
      {value.map((s, i) =>
        typeof s === "string" ? (
          <Fragment key={i}>{s}</Fragment>
        ) : (
          <b key={i}>{s.b}</b>
        ),
      )}
    </>
  );
}
```

- [ ] **Step 4: Run — expect pass**

Run: `npm test -- rich-text 2>&1 | tail -5`
Expected: PASS (2 tests).

- [ ] **Step 5: Implement `types.ts`** (exactly spec §4.2)

```ts
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
export interface QueryPreset extends DiscoverData { chip: string; }
export interface QueryChip { id: string; icon: string; label: string; }
export interface ComposerModel { id: string; name: string; desc: string; icon: string; lat: string; }
```

- [ ] **Step 6: Write the failing data-contract test**

`web/src/lib/discover/__tests__/mock.test.ts`:
```ts
import { BASE_DATA, QUERY_PRESETS, QUERY_CHIPS } from "../mock";

test("BASE_DATA shape", () => {
  expect(BASE_DATA.alerts).toHaveLength(3);
  expect(BASE_DATA.minis).toHaveLength(3);
  expect(BASE_DATA.funnel.blocks).toHaveLength(5);
  expect(BASE_DATA.funnel.arrows).toHaveLength(4);
  expect(BASE_DATA.minis[0].lab).toBe("Brand-cited answers");
  expect(BASE_DATA.minis[0].v).toBe("94"); // v1 bug fixed: not 284
  expect(BASE_DATA.funnel.blocks.filter((b) => b.here)).toHaveLength(1);
});

test("presets are full overrides with a chip label", () => {
  for (const id of ["mortgage", "competitor"] as const) {
    const p = QUERY_PRESETS[id];
    expect(typeof p.chip).toBe("string");
    expect(p.alerts).toHaveLength(3);
    expect(p.funnel.blocks).toHaveLength(5);
  }
});

test("missing chip is unwired", () => {
  const missing = QUERY_CHIPS.find((c) => c.id === "missing");
  expect(missing).toBeTruthy();
  expect(QUERY_PRESETS["missing" as keyof typeof QUERY_PRESETS]).toBeUndefined();
});
```

- [ ] **Step 7: Run — expect fail**

Run: `npm test -- discover/__tests__/mock 2>&1 | tail -5`
Expected: FAIL (`Cannot find module '../mock'`).

- [ ] **Step 8: Implement `mock.ts`** — transcribe **verbatim** from `/tmp/cortex-handoff/cortex/project/cortex/dashboard.jsx` (`BASE_DATA` lines 127–197, `QUERY_PRESETS` 199–344, `QUERY_CHIPS` 346–350) and `cortex-composer.jsx` `MODELS` (lines 7–12). Convert every JSX rich value to `RichText`:
- `<><b>X</b> · y</>` → `[{ b: "X" }, " · y"]`
- headline `<><b>8 brand answers missing</b> on tracked questions</>` → `[{ b: "8 brand answers missing" }, " on tracked questions"]`
- multi-bold takeaway → spans in order, e.g. `<>Only <b>1 in 9</b> questions … the <b>8 missing answers</b> …</>` → `["Only ", { b: "1 in 9" }, " questions … the ", { b: "8 missing answers" }, " …"]`
Types: `export const BASE_DATA: DiscoverData = {…}`, `export const QUERY_PRESETS: Record<"mortgage" | "competitor", QueryPreset> = {…}`, `export const QUERY_CHIPS: QueryChip[] = [{ id:"mortgage", icon:"home_work", label:"Show me mortgage topics" }, { id:"competitor", icon:"compare_arrows", label:"Compare to Competitor A" }, { id:"missing", icon:"report_problem", label:"Where am I missing answers?" }]`, `export const COMPOSER_MODELS: ComposerModel[] = [{ id:"gemini-flash", name:"Gemini 2.5 Flash", desc:"Lowest latency, low cost", icon:"bolt", lat:"23ms" }, { id:"gemini-pro", name:"Gemini 2.5 Pro", desc:"General reasoning, multimodal", icon:"memory", lat:"84ms" }, { id:"claude-opus", name:"Claude Opus 4.7", desc:"Highest reasoning quality", icon:"psychology", lat:"312ms" }, { id:"gpt-5", name:"GPT-5", desc:"Broad capability, tool use", icon:"developer_mode", lat:"156ms" }]`.

- [ ] **Step 9: Run — expect pass**

Run: `npm test -- discover/__tests__ 2>&1 | tail -5`
Expected: PASS (rich-text 2 + mock 3).

- [ ] **Step 10: Commit**

```bash
git add src/lib/discover/
git commit -m "$(cat <<'EOF'
feat(discover): serializable v2 data contract (RichText + BASE_DATA/QUERY_PRESETS)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

## Task F3: BrandShell drawer state + ⌘K/Esc + 3-col grid

**Files:**
- Create: `web/src/components/brand-dashboard/discover/drawer-context.tsx`
- Modify: `web/src/components/shell/brand-shell.tsx`
- Test: `web/src/components/brand-dashboard/discover/__tests__/drawer-context.test.tsx`

- [ ] **Step 1: Write the failing context/hook test**

`__tests__/drawer-context.test.tsx`:
```tsx
import { render, screen, act } from "@testing-library/react";
import { DrawerProvider, useCortexDrawer } from "../drawer-context";

function Probe() {
  const d = useCortexDrawer();
  return (
    <>
      <span data-testid="open">{String(d.drawerOpen)}</span>
      <button onClick={d.openDrawer}>open</button>
      <button onClick={d.closeDrawer}>close</button>
    </>
  );
}

test("opens and closes", () => {
  render(<DrawerProvider><Probe /></DrawerProvider>);
  expect(screen.getByTestId("open").textContent).toBe("false");
  act(() => screen.getByText("open").click());
  expect(screen.getByTestId("open").textContent).toBe("true");
  act(() => screen.getByText("close").click());
  expect(screen.getByTestId("open").textContent).toBe("false");
});

test("Escape closes; Cmd/Ctrl+K toggles", () => {
  render(<DrawerProvider><Probe /></DrawerProvider>);
  act(() => window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", metaKey: true })));
  expect(screen.getByTestId("open").textContent).toBe("true");
  act(() => window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" })));
  expect(screen.getByTestId("open").textContent).toBe("false");
});
```

- [ ] **Step 2: Run — expect fail**

Run: `npm test -- drawer-context 2>&1 | tail -5`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement `drawer-context.tsx`**

```tsx
"use client";
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

interface CortexDrawerValue {
  drawerOpen: boolean;
  openDrawer: () => void;
  closeDrawer: () => void;
  toggleDrawer: () => void;
  value: string;
  setValue: (v: string) => void;
  model: string;
  setModel: (m: string) => void;
}
const Ctx = createContext<CortexDrawerValue | null>(null);

export function DrawerProvider({ children }: { children: ReactNode }) {
  const [drawerOpen, setOpen] = useState(false);
  const [value, setValue] = useState("");
  const [model, setModel] = useState("auto");
  const openDrawer = useCallback(() => setOpen(true), []);
  const closeDrawer = useCallback(() => setOpen(false), []);
  const toggleDrawer = useCallback(() => setOpen((o) => !o), []);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") { setOpen(false); return; }
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const v = useMemo<CortexDrawerValue>(
    () => ({ drawerOpen, openDrawer, closeDrawer, toggleDrawer, value, setValue, model, setModel }),
    [drawerOpen, openDrawer, closeDrawer, toggleDrawer, value, model],
  );
  return <Ctx.Provider value={v}>{children}</Ctx.Provider>;
}

export function useCortexDrawer(): CortexDrawerValue {
  const c = useContext(Ctx);
  if (!c) throw new Error("useCortexDrawer must be used within DrawerProvider");
  return c;
}
```

- [ ] **Step 4: Run — expect pass**

Run: `npm test -- drawer-context 2>&1 | tail -5`
Expected: PASS (2 tests).

- [ ] **Step 5: Wire into `brand-shell.tsx`**

Wrap the existing `.geo-app` subtree in `<DrawerProvider>`. Add `data-drawer-open` from `useCortexDrawer().drawerOpen` (render `"true"` or omit). Render `<AskCortexTrigger/>` and `<CortexDrawer/>` as shell-level siblings (created in R6 — until then, add `{/* R6: <AskCortexTrigger/> <CortexDrawer/> */}` placeholders **only as TODO markers removed in R6**, and keep `data-drawer-open` wired so F1 CSS is exercised). Exact edit: read current `brand-shell.tsx`, add the attribute on the `.geo-app` div and the provider wrapper; do not change sidebar-collapse logic.

- [ ] **Step 6: Verify**

Run: `npm run lint && npm run type-check 2>&1 | grep -c "error TS" && npm test -- drawer-context 2>&1 | tail -3`
Expected: lint clean; TS error count == baseline; tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/components/brand-dashboard/discover/drawer-context.tsx src/components/brand-dashboard/discover/__tests__/drawer-context.test.tsx src/components/shell/brand-shell.tsx
git commit -m "$(cat <<'EOF'
feat(discover): lift Cortex drawer state into BrandShell (Cmd-K/Esc, 3-col grid)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

## Task F4: Sidebar §04 rework

**Files:**
- Modify: `web/src/components/shell/sidebar.tsx`
- Test: `web/src/components/shell/__tests__/sidebar.test.tsx`

- [ ] **Step 1: Write the failing test** (spec §9)

`web/src/components/shell/__tests__/sidebar.test.tsx`:
```tsx
import { render, screen } from "@testing-library/react";
import { Sidebar } from "../sidebar";

const props = {
  activeContextKind: "brand" as const, role: "admin" as const, tier: "enterprise" as const,
  user: { displayName: "CMO / Wang", orgName: "Acme Bank Asia", initial: "王" },
};

test("v2 §04 sidebar shows the right items", () => {
  render(<Sidebar {...props} />);
  for (const label of ["Discover", "History", "Media Network", "Knowledge Base", "Brand Voice", "Connectors"])
    expect(screen.getByText(label)).toBeInTheDocument();
});

test("v2 removes New decision / GEO Monitor / status pod / Enterprise pill", () => {
  render(<Sidebar {...props} />);
  expect(screen.queryByText(/New decision/i)).toBeNull();
  expect(screen.queryByText("GEO Monitor")).toBeNull();
  expect(screen.queryByText(/Brand Cortex/i)).toBeNull(); // status pod gone
  expect(screen.queryByText(/Enterprise/i)).toBeNull();
});
```

- [ ] **Step 2: Run — expect fail**

Run: `npm test -- shell/__tests__/sidebar 2>&1 | tail -5`
Expected: FAIL (current file is the trimmed Discover-only sidebar w/ status pod).

- [ ] **Step 3: Rewrite `sidebar.tsx` to §04**

Restore the §04 nav model on the existing Aurora Mist `.sb` markup. `NAV` = ungrouped top `[{label:"Discover",icon:"grid_view",href:"/brand/dashboard",isDefault:true,requires:"view_brand_dashboard"},{label:"History",icon:"schedule",href:"/brand/history",requires:"view_brand_dashboard"}]`; section `Network` → `[{label:"Media Network",icon:"hub",href:"/brand/dashboard",requires:"view_brand_dashboard"}]`; section `Agent` → `[{label:"Knowledge Base",icon:"menu_book",href:"/knowledge",requires:"view_kb_enterprise"},{label:"Brand Voice",icon:"campaign",href:"/brand/dashboard",requires:"view_brand_dashboard"},{label:"Connectors",icon:"cable",href:"/connectors",requires:"view_connectors"}]`. Keep `hasCapability` filter + `isItemActive` (exact match for `isDefault`). **Remove**: `NEW_DECISION` CTA, the status `pod`, ENT `Badge`/`pill`, GEO Monitor, MONITOR/CONTENT sections. Keep logo, collapse chevron, user footer (avatar/name/org/gear), `SignOutButton`. `SidebarProps` unchanged (drop now-unused `health` usage but keep the optional prop to avoid consumer churn — or remove if no consumer passes it; `grep -n "health=" src` first). Update the file's doc-comment to the v2 IA.

- [ ] **Step 4: Run — expect pass + suite**

Run: `npm test -- shell/__tests__/sidebar 2>&1 | tail -5 && npm run lint && npm run type-check 2>&1 | grep -c "error TS"`
Expected: sidebar tests PASS; lint clean; TS count == baseline.

- [ ] **Step 5: Commit**

```bash
git add src/components/shell/sidebar.tsx src/components/shell/__tests__/sidebar.test.tsx
git commit -m "$(cat <<'EOF'
feat(discover): sidebar §04 — supersede Discover-only trim

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

# PHASE 1 — Regions (parallelizable after Phase 0)

> Each region renders from a `DiscoverData` prop. Pixel values: spec §6.x +
> verbatim `/tmp/cortex-handoff/cortex/project/cortex/discover.css`. Classes already
> exist (Task F1). Each task: behavior test → component → render-smoke → visual
> check → commit.

## Task R1: Topbar + Priority alerts

**Files:**
- Create: `web/src/components/brand-dashboard/discover/topbar.tsx`, `priority-alerts.tsx`
- Test: `__tests__/priority-alerts.test.tsx`

- [ ] **Step 1: Failing alerts test**
```tsx
import { render, screen } from "@testing-library/react";
import { PriorityAlerts } from "../priority-alerts";
import { BASE_DATA } from "@/lib/discover/mock";

test("renders 3 intent-coded alert cards", () => {
  const { container } = render(<PriorityAlerts alerts={BASE_DATA.alerts} />);
  expect(container.querySelectorAll(".alert")).toHaveLength(3);
  expect(container.querySelector(".alert.is-warn")).toBeTruthy();
  expect(container.querySelector(".alert.is-opp")).toBeTruthy();
  expect(container.querySelector(".alert.is-sig")).toBeTruthy();
  expect(screen.getByText("GAP")).toBeInTheDocument();
});
```
- [ ] **Step 2: Run — expect fail.** `npm test -- priority-alerts` → module not found.
- [ ] **Step 3: Implement `priority-alerts.tsx`** — `<div className="alerts">` of 3 `<article className={"alert is-"+a.kind}>` with `.alert-head` (icon `material-icons-outlined` + `.alert-cat`), `.alert-body` `<Rich value={a.headline}/>`, `.alert-sub`, `.alert-cta` button. Markup mirrors `dashboard.jsx` lines 434–446.
- [ ] **Step 4: Implement `topbar.tsx`** — `.sp .top` with `.left .page-title` (`.crumb` "BRAND CORTEX", `<h1>Discover</h1>`, `.subtitle` + `.muted` freshness), `.right` filter chips (`All markets`, `Last 30 days` `is-on`) + Export `.btn`. Mirrors `dashboard.jsx` 409–431; static (filters non-functional per spec §8).
- [ ] **Step 5: Run — expect pass.** `npm test -- priority-alerts` → PASS.
- [ ] **Step 6: Commit** `git add` the 3 files →
```
feat(discover): topbar + priority alerts region
```

## Task R2: Cortex query strip

**Files:** Create `cortex-query-strip.tsx`; Test `__tests__/cortex-query-strip.test.tsx`.

- [ ] **Step 1: Failing test**
```tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { CortexQueryStrip } from "../cortex-query-strip";

test("suggest → applied toggle + callbacks", () => {
  const onQuery = vi.fn(); const onClear = vi.fn();
  const { rerender, container } = render(
    <CortexQueryStrip activeQuery={null} onQuery={onQuery} onClear={onClear} />,
  );
  fireEvent.click(screen.getByText("Show me mortgage topics"));
  expect(onQuery).toHaveBeenCalledWith("mortgage");
  rerender(<CortexQueryStrip activeQuery="mortgage" onQuery={onQuery} onClear={onClear} />);
  expect(container.querySelector(".cq-applied")).toBeTruthy();
  fireEvent.click(screen.getByLabelText("Clear filter"));
  expect(onClear).toHaveBeenCalled();
});

test("missing chip is disabled", () => {
  render(<CortexQueryStrip activeQuery={null} onQuery={vi.fn()} onClear={vi.fn()} />);
  expect(screen.getByText("Where am I missing answers?").closest("button")).toBeDisabled();
});
```
- [ ] **Step 2: Run — expect fail.**
- [ ] **Step 3: Implement** from `dashboard.jsx` `CortexQueryStrip` (352–399): `.cq-bar` (`.cq-mark` auto_awesome, `.cq-input` placeholder switches on `activeQuery`, `.cq-version`), then `.cq-applied` (when `activeQuery`: label + `QUERY_PRESETS[id].chip` + `.cq-clear`) else `.cq-suggest` (`QUERY_CHIPS` → `.cq-chip`, `disabled={!QUERY_PRESETS[id]}`).
- [ ] **Step 4: Run — expect pass.**
- [ ] **Step 5: Commit** → `feat(discover): Cortex query strip`

## Task R3: KPI row + sparklines

**Files:** Create `kpi-row.tsx`, `hero-sparkline.tsx`, `mini-sparkline.tsx`; Test `__tests__/kpi-row.test.tsx`.

- [ ] **Step 1: Failing test**
```tsx
import { render, screen } from "@testing-library/react";
import { KpiRow } from "../kpi-row";
import { BASE_DATA } from "@/lib/discover/mock";

test("renders hero value + 3 minis with sparklines", () => {
  const { container } = render(<KpiRow hero={BASE_DATA.hero} minis={BASE_DATA.minis} />);
  expect(screen.getByText("18.4")).toBeInTheDocument();
  expect(screen.getByText("Brand-cited answers")).toBeInTheDocument();
  expect(container.querySelectorAll(".mini")).toHaveLength(3);
  expect(container.querySelectorAll(".mini-spk")).toHaveLength(3);
  expect(container.querySelector(".h-main .spk")).toBeTruthy();
});
```
- [ ] **Step 2: Run — expect fail.**
- [ ] **Step 3: Implement** `hero-sparkline.tsx` (SVG 480×180, gradient `#1C726B` 0.18→0, stroke 2px — verbatim `dashboard.jsx` 65–84), `mini-sparkline.tsx` (140×28, stroke 1.5px round, `trend` point sets — verbatim 104–120), `kpi-row.tsx` `.hero` grid: `.card.h-main` (`.lab`+`.live`, `.v`+`<sup>`, `.sub` `.up`+note, `<HeroSparkline/>`) + 3 `.card.mini` (`.lab`,`.v`,`.row b`,`<MiniSparkline trend=…/>`). Mirrors 456–479.
- [ ] **Step 4: Run — expect pass.**
- [ ] **Step 5: Commit** → `feat(discover): KPI row with hero/mini sparklines`

## Task R4: GEO funnel

**Files:** Create `geo-funnel.tsx`, `funnel-arrow.tsx`; Test `__tests__/geo-funnel.test.tsx`.

- [ ] **Step 1: Failing test**
```tsx
import { render } from "@testing-library/react";
import { GeoFunnel } from "../geo-funnel";
import { BASE_DATA } from "@/lib/discover/mock";

test("5 blocks, 4 arrows, one is-here, bottleneck+leverage", () => {
  const { container } = render(<GeoFunnel funnel={BASE_DATA.funnel} />);
  expect(container.querySelectorAll(".blk")).toHaveLength(5);
  expect(container.querySelectorAll(".conn")).toHaveLength(4);
  expect(container.querySelectorAll(".blk.is-here")).toHaveLength(1);
  expect(container.querySelector(".conn.is-bottleneck")).toBeTruthy();
  expect(container.querySelector(".conn.is-leverage")).toBeTruthy();
  expect(container.querySelector(".fnl-takeaway")).toBeTruthy();
});
```
- [ ] **Step 2: Run — expect fail.**
- [ ] **Step 3: Implement** from `dashboard.jsx` 482–511 + `FunnelArrow` 86–101: `.funnel`→`.fh`→`.flow` interleaving `blocks[i]` (`.blk` + `.is-here` + `.v`/`.nm` `<Rich/>` + `.badge`) with `<FunnelArrow rate label kind/>` for `i<arrows.length`; `.fnl-takeaway` (lightbulb + `<Rich value={funnel.takeaway}/>` + `<a>` `takeawayCta`).
- [ ] **Step 4: Run — expect pass.**
- [ ] **Step 5: Commit** → `feat(discover): GEO funnel + bottleneck/leverage + takeaway`

## Task R5: Media + Competitor grid

**Files:** Create `media-competitor-grid.tsx`; Test `__tests__/media-competitor-grid.test.tsx`.

- [ ] **Step 1: Failing test**
```tsx
import { render, screen } from "@testing-library/react";
import { MediaCompetitorGrid } from "../media-competitor-grid";
import { BASE_DATA } from "@/lib/discover/mock";

test("media rows + competitor h2h with you/lead", () => {
  const { container } = render(<MediaCompetitorGrid media={BASE_DATA.media} comp={BASE_DATA.comp} />);
  expect(container.querySelectorAll(".media .row:not(.head)")).toHaveLength(5);
  expect(container.querySelector(".h2h.you")).toBeTruthy();
  expect(container.querySelector(".h2h.lead")).toBeTruthy();
  expect(screen.getByText("−15.8 pp")).toBeInTheDocument();
});
```
- [ ] **Step 2: Run — expect fail.**
- [ ] **Step 3: Implement** from `dashboard.jsx` 514–572: `.grid` → `.card.media` (`.ch` header + link, `.row.head`, rows: `.rk`/`.nm`+`.badge`/`.bar i width:${vis*2.4}%`/`.pct`/`.clk`) + `.card.comp` (`.ch`, `.h2h` w/ `.you`/`.lead`, `.track i width:${pct*2.4}%`+`.lbl`, `.legend` trending_down + `comp.gap`).
- [ ] **Step 4: Run — expect pass.**
- [ ] **Step 5: Commit** → `feat(discover): media + competitor grid`

## Task R6: Docked drawer + ⌘K trigger + composer

**Files:** Create `composer-card.tsx`, `model-picker.tsx`, `cortex-drawer.tsx`, `ask-cortex-trigger.tsx`; keep `cortex-mark.tsx`; Modify `brand-shell.tsx` (replace R6 TODO markers with real mounts); Test `__tests__/cortex-drawer.test.tsx`.

- [ ] **Step 1: Failing test**
```tsx
import { render, screen, act } from "@testing-library/react";
import { DrawerProvider } from "../drawer-context";
import { AskCortexTrigger } from "../ask-cortex-trigger";
import { CortexDrawer } from "../cortex-drawer";

test("trigger opens the docked drawer; Esc closes", () => {
  render(<DrawerProvider><AskCortexTrigger /><CortexDrawer /></DrawerProvider>);
  expect(screen.queryByRole("dialog")).toBeNull();
  act(() => screen.getByRole("button", { name: /Ask Cortex/i }).click());
  expect(screen.getByRole("dialog")).toBeInTheDocument();
  act(() => window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" })));
  expect(screen.queryByRole("dialog")).toBeNull();
});
```
- [ ] **Step 2: Run — expect fail.**
- [ ] **Step 3: Implement** from `cortex-composer.jsx`: `model-picker.tsx` (`ModelPill` + portaled `ModelPicker` `.mdl-pop`, `COMPOSER_MODELS` + Auto), `composer-card.tsx` (`.cmp` input + `.cmp-foot`), `cortex-drawer.tsx` (`.cmp-drawer` `role="dialog"`, `.head`/`.empty` 4 `DRAWER_QUICK` + `.foot` `<ComposerCard/>`; reads `useCortexDrawer()`; **does not unmount on close** — render always, toggle a class/attr; backdrop element present but CSS-hidden when docked via F1), `ask-cortex-trigger.tsx` (`.cmp-drawer-trigger` `<CortexMark size={24}/>` + "Ask Cortex"; `onClick=openDrawer`; CSS hides it when `data-drawer-open`). `DRAWER_QUICK = ["本週品牌曝光走勢","未覆蓋話題清單","競品差距分析","派工給 Answer Pilot"]` (verbatim `cortex-composer.jsx` 22–27). Replace the F3 TODO markers in `brand-shell.tsx` with `<AskCortexTrigger/>` + `<CortexDrawer/>`.
- [ ] **Step 4: Run — expect pass + suite.** `npm test -- cortex-drawer && npm run lint && npm run type-check 2>&1 | grep -c "error TS"` → tests PASS, lint clean, count == baseline.
- [ ] **Step 5: Commit** → `feat(discover): docked Cortex drawer + ⌘K trigger + composer`

## Task R7: EmptyDiscover v2 re-skin

**Files:** Modify `web/src/components/brand-dashboard/empty-discover.tsx`; Test (extend) `__tests__/empty-discover.test.tsx` if present else create a render smoke.

- [ ] **Step 1: Smoke test stays green**
```tsx
import { render } from "@testing-library/react";
import { EmptyDiscover } from "../empty-discover";
test("renders without crashing", () => { render(<EmptyDiscover />); });
```
- [ ] **Step 2: Run baseline** `npm test -- empty-discover` → PASS (pre-change).
- [ ] **Step 3: Re-skin** — swap ad-hoc colors/spacing for v2 tokens/recipes (`var(--mly-*)`, `.sp .card`, alert/funnel-skeleton classes from F1); **do not change logic/props/data-source or the `connectedSourceCount===0 && !demo` gate**. No loading/error states (spec §8).
- [ ] **Step 4: Run — still PASS** + `npm run lint && npm run type-check 2>&1 | grep -c "error TS"` (== baseline).
- [ ] **Step 5: Commit** → `style(discover): re-skin EmptyDiscover to v2 tokens`

---

# PHASE 2 — Integration, cleanup, verification

## Task I1: Assemble DiscoverDashboard + wire the page

**Files:** Create `discover-dashboard.tsx`; Modify `web/src/app/brand/dashboard/page.tsx`; Test `__tests__/discover-dashboard.test.tsx`.

- [ ] **Step 1: Failing integration test**
```tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { DrawerProvider } from "../drawer-context";
import { DiscoverDashboard } from "../discover-dashboard";

const ui = () => render(<DrawerProvider><DiscoverDashboard /></DrawerProvider>);

test("query swap re-shapes hero + alerts in place", () => {
  ui();
  expect(screen.getByText("18.4")).toBeInTheDocument();           // BASE_DATA hero
  fireEvent.click(screen.getByText("Show me mortgage topics"));
  expect(screen.getByText("22.1")).toBeInTheDocument();           // mortgage preset hero
  fireEvent.click(screen.getByLabelText("Clear filter"));
  expect(screen.getByText("18.4")).toBeInTheDocument();           // restored
});
```
- [ ] **Step 2: Run — expect fail.**
- [ ] **Step 3: Implement `discover-dashboard.tsx`** — `"use client"`; `const [activeQuery,setActiveQuery]=useState<string|null>(null)`; `const data = activeQuery ? QUERY_PRESETS[activeQuery as "mortgage"|"competitor"] : BASE_DATA`; render `<div className="pg sp">` with `<Topbar/>`, `<PriorityAlerts key={"alerts-"+(activeQuery??"base")} alerts={data.alerts}/>`, `<CortexQueryStrip activeQuery={activeQuery} onQuery={setActiveQuery} onClear={()=>setActiveQuery(null)}/>`, `<KpiRow key={activeQuery??"base"} hero={data.hero} minis={data.minis}/>`, `<GeoFunnel funnel={data.funnel}/>`, `<MediaCompetitorGrid media={data.media} comp={data.comp}/>`. (Trigger+drawer already at shell level from R6.)
- [ ] **Step 4: Modify `page.tsx`** — render `<DiscoverDashboard/>` for the populated/demo path; keep the existing `connectedSourceCount===0 && !demo` → `<EmptyDiscover/>` gate exactly as today.
- [ ] **Step 5: Run — expect pass.** `npm test -- discover-dashboard` → PASS.
- [ ] **Step 6: Commit** → `feat(discover): assemble DiscoverDashboard + wire /brand/dashboard`

## Task I2: Delete superseded v1.2 code

**Files:** Delete per File Structure; Modify any stragglers.

- [ ] **Step 1: Find consumers** `cd web && git grep -nE "discover-mock|brand-dashboard/discover/sections|discover/cortex-composer|cortex-prompt|brand-dashboard/(kpi-card|funnel-card|time-range-filter|publisher-breakdown-table)"`
- [ ] **Step 2: Migrate/remove** remaining imports to the new modules; delete only files with zero remaining importers.
- [ ] **Step 3: Delete** the confirmed-dead files (`git rm`).
- [ ] **Step 4: Verify** `npm run lint && npm run type-check 2>&1 | grep -c "error TS" && npm test 2>&1 | tail -3`
Expected: lint clean; TS count == baseline (2); full suite green (≥ Task 0 count + new tests).
- [ ] **Step 5: Commit** → `refactor(discover): remove superseded v1.2 Discover code`

## Task I3: Full verification + visual pass

**Files:** none (verification); fixes commit under the relevant region.

- [ ] **Step 1: Suite gate** `npm run lint && npm run type-check 2>&1 | grep "error TS" | sort > /tmp/tsc.now` then `diff <(printf '%s\n' 'src/app/(auth)/onboarding/manual/page.tsx' 'src/app/(auth)/onboarding/page.tsx' ) <(cut -d'(' -f1 /tmp/tsc.now | sort -u)` — only the 2 known files; `npm test` fully green.
- [ ] **Step 2: Visual check** Start dev with `.env.local` `NEXT_PUBLIC_DEV_BYPASS_AUTH=true`; one dev server on :3000; Playwright navigate `/brand/dashboard`, viewport 1440. Accessibility snapshot + screenshot per region. Verify against spec §6 / acceptance checklist §11: sidebar §04; topbar crumb/H1; 3 alerts; query swap (click "Show me mortgage topics" → hero 22.1, `.cq-applied`, clear restores); KPI sparklines + "Brand-cited answers" 94; funnel 5+4, bottleneck red / leverage green, takeaway; media/competitor YOU/LEADER; ⌘K opens **docked** drawer (3rd column, no scrim, trigger hidden), Esc closes; EmptyDiscover (force `connectedSourceCount=0`) re-skinned.
- [ ] **Step 3: Fix-forward** any mismatch under the owning region task; re-run Steps 1–2.
- [ ] **Step 4: Final commit** (only if Step 3 produced fixes) → `fix(discover): visual-parity corrections`

---

## Self-Review

**1. Spec coverage:** §1 decisions → Task 0/F1–F4/I2 (decisions 5/6/7/8) ✓ · §2 architecture → F3 ✓ · §3 tokens/recipes → F1 ✓ · §4 data contract → F2 ✓ · §5 file map → File Structure + all tasks ✓ · §6 region pixels → R1–R6 ✓ · §7 interactions → R2/F3/I1 ✓ · §8 out-of-scope → respected (no mobile/loading/error/Tweaks) ✓ · §9 sidebar → F4 ✓ · §10 decomposition → Phase 0/1/2 mirrors it ✓ · §11 testing/acceptance → I3 + per-task tests ✓ · §12 risks (globals surgery scoped, §02/§14 tension = no in-stage hero) → F1 Step 3 + R6 ✓.

**2. Placeholder scan:** No "TBD/TODO/handle edge cases". Verbatim-transcription steps cite exact source files + line ranges + the committed spec §6 — that is a concrete instruction, not a placeholder. The R6 TODO markers in F3 are explicitly created-then-removed within F3/R6 (not left dangling).

**3. Type consistency:** `DiscoverData`/`Alert`/`Hero`/`Mini`/`FunnelBlock`/`FunnelArrow`/`MediaRow`/`CompRow`/`QueryPreset`/`QueryChip`/`ComposerModel` defined once in F2 Step 5 and consumed unchanged in R1–R6/I1. `useCortexDrawer()` shape defined in F3 Step 3, consumed in R6/brand-shell. `RichText`/`<Rich>` defined F2 Step 3, consumed R1/R4. Component prop names (`alerts`, `hero`, `minis`, `funnel`, `media`, `comp`, `activeQuery`/`onQuery`/`onClear`) consistent between region tasks and I1 assembly.

No gaps found.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-20-cortex-discover-v2.md`. Per the user's chosen workflow (spec → plan → **subagent-driven parallel execution**): execute Phase 0 serially, then Phase 1 R1–R7 as parallel subagents, then Phase 2, with two-stage review between tasks (subagent-driven-development).
