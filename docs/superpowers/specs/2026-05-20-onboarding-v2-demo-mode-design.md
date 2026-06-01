# Onboarding v2 Demo Mode — Design Spec

**Date:** 2026-05-20
**Revised:** 2026-05-20 (post-implementation: corrected for actual `/onboarding/v2` shape on `develop`)
**Audience:** GTM / CEO live demos and pre-meeting URL drops
**Scope:** A public, auth-free clone of the `/onboarding/v2` flow served at `/demo/onboarding`, driven by the existing `MockOnboardingApi` adapter, with English and Traditional Chinese parity.

---

## 1. Problem & motivation

The existing `/onboarding/v2` flow on `develop` is **API-driven** through a typed `OnboardingApi` seam (`web/src/lib/onboarding/api.ts`). The page's `getOnboardingApi()` factory returns one of two adapters based on a build-time flag: `MockOnboardingApi` (default — returns the constants in `data.ts`) or `HttpOnboardingApi` (real cortex-api calls, gated by `NEXT_PUBLIC_CORTEX_ONBOARDING_HTTP=1`). The mock adapter resolves immediately and gives byte-for-byte the same UX as the original hardcoded version.

So the flow is *almost* a demo today. Three things stand in the way:

1. **Auth wall.** The page lives under the `(auth)` route group and the terminal CTA calls a server action `completeV2Onboarding` that requires a signed-in session and an active brand context (`session.user.activeContext.kind === "brand"`). A CEO walking in cold can't reach the success screen.
2. **Production build defaults to HTTP adapter.** In a real build with `NEXT_PUBLIC_CORTEX_ONBOARDING_HTTP=1`, `getOnboardingApi()` returns the HTTP adapter — which hits real cortex-api endpoints, requires auth, and tries to persist data. The demo flow must force the mock adapter regardless of the build flag.
3. **Terminal CTA navigates to `/brand/dashboard`.** Even if a CEO could authenticate, the dashboard requires brand membership and live data.

The wizard's API-driven shape is good news for this feature: we can lift it into a shared client component that takes the `OnboardingApi` adapter **as a prop**, and the demo page injects a forced `new MockOnboardingApi()`. The live page injects `getOnboardingApi()` (the factory). No global mocking, no env-flag wrangling — dependency injection at one prop.

GTM needs a URL they can send before a meeting and re-run on stage without setting up Google accounts or worrying about stale browser state. CEO needs the same flow to demonstrate the product narrative end to end.

## 2. Goals & non-goals

**In scope:**
- New public routes `/demo/onboarding` (en) and `/demo/onboarding/zh-TW` (zh) that render the existing wizard with mock data.
- No authentication, no session, no cortex-api calls.
- Always boot at step 0 — the live page already does this (storage rehydrate was removed for the same reason), so the demo just preserves that behaviour.
- Terminal CTA restarts the demo instead of running the `completeV2Onboarding` server action and pushing into the authenticated app.
- A subtle "Demo" pill in the topbar so the mode is honest in screenshots.
- Both languages reach feature parity in the same PR.

**Out of scope:**
- New mock data. The existing `MockOnboardingApi` (which already returns `EXTRACTED_BRAND`, `MEDIA_NETWORK`, etc. from `data.ts`) is reused as-is.
- New step components or step copy. The demo is a behaviour delta over the live wizard, not a divergent UI.
- A language toggle inside the demo (the existing `EN | 繁中` link in the topbar is rewired but not redesigned).
- Discoverability — the demo is link-only. No nav entry, no marketing CTA, no token gate.
- A separate demo dashboard. The terminal CTA on the "Brand Agent online" screen becomes a Restart button; it does not deep-link to a populated insights view.
- E2E browser tests. Manual walkthrough before sales calls is the acceptance bar.

## 3. Decisions captured during brainstorming

| # | Decision | Why |
|---|---|---|
| D1 | Route layout: public `/demo/onboarding` (+ `zh-TW`), outside `(auth)` | Mirrors the existing `/demo` (Daohe) pattern, no middleware to fight. |
| D2 | Terminal CTA: Restart only, no `router.push` | A CEO will not have a signed-in brand context; bouncing them to `/brand/dashboard` from a demo dead-ends the meeting. |
| D3 | State on reload: always start fresh from step 0 | Demos should be reproducible. The next user reloads and the wizard is clean. |
| D4 | Visual signal: subtle "Demo" pill in the topbar | Reads honest in screenshots, doesn't eat layout, doesn't undercut polish. |
| D5 | Seeded brand: same `EXTRACTED_BRAND` (Acme Bank Asia) as today | No new mock data set, no new translation work, no drift. |
| D6 | Discoverability: link-only, no marketing entry | Standard pattern for sales demos; protects the URL from anonymous indexing. |
| D7 | Implementation approach: shared `<OnboardingV2Wizard>` with `mode`, `api`, `onComplete` props (Approach A, revised) | Single source of truth across live and demo. The wizard takes the `OnboardingApi` adapter as a prop (DI) so the demo route forces the Mock adapter without env wrangling. |

## 4. Architecture

Thin route files per language, one shared client component per language, plus a server/client split on each demo route so the demo page can export `metadata` for the tab title.

```
web/src/
├─ app/
│  ├─ (auth)/onboarding/v2/
│  │  ├─ page.tsx                     ← MODIFIED: useMemo(() => getOnboardingApi(), []) → <OnboardingV2Wizard mode="live" api onComplete={completeV2Onboarding} />
│  │  └─ zh-TW/page.tsx               ← MODIFIED: same shape, uses zh wizard
│  └─ demo/onboarding/
│     ├─ page.tsx                     ← NEW (server component): exports metadata, renders <DemoOnboardingClient />
│     ├─ client.tsx                   ← NEW (client component): useMemo(() => new MockOnboardingApi(), []) → <OnboardingV2Wizard mode="demo" api />
│     └─ zh-TW/
│        ├─ page.tsx                  ← NEW (server): metadata + <DemoOnboardingZhClient />
│        └─ client.tsx                ← NEW (client): zh wizard with mock api
├─ components/onboarding-v2/
│  ├─ wizard.tsx                      ← NEW: lifted body of (auth)/onboarding/v2/page.tsx, takes { mode, api, onComplete? }
│  ├─ primitives.tsx                  ← MODIFIED in Task 1: <TopBar> gains showDemoBadge?: boolean + langSwitchHref props
│  └─ step-*.tsx, data.ts, launch-overlay.tsx — unchanged
├─ components/onboarding-v2-zh/
│  ├─ wizard.tsx                      ← NEW: lifted body of zh-TW page, takes { mode, api, onComplete? }
│  ├─ primitives.tsx                  ← MODIFIED in Task 2: same two new props
│  └─ step-*.tsx, data.ts, launch-overlay.tsx — unchanged
└─ lib/onboarding/
   ├─ api.ts                          — unchanged (still has getOnboardingApi factory)
   ├─ mock-api.ts                     — unchanged (exports MockOnboardingApi, used directly by demo pages)
   └─ http-api.ts                     — unchanged
```

**Why the server/client split on the demo route.** Next App Router only respects `export const metadata` on **server components**. The wizard wiring needs `useMemo` (to instantiate the API adapter exactly once for the component lifetime), which requires a client component. Splitting the page into a server-component wrapper (`page.tsx`) that exports `metadata` and renders a client child (`client.tsx`) is the standard pattern. The live page does NOT split — it doesn't export metadata, so it stays as a single client component.

The `(auth)` route group has no `layout.tsx` and Cortex has no `middleware.ts` — `(auth)` is decorative. Adding a sibling `/demo/onboarding` route is a plain new route; no auth bypass is required.

## 5. The wizard prop surface

The wizard takes three props. `mode` documents intent and gates a handful of UI/behaviour branches. `api` and `onComplete` are the dependency-injection surface that lets the demo route avoid both the HTTP adapter and the server action.

```ts
type WizardMode = "live" | "demo";

interface OnboardingV2WizardProps {
  mode: WizardMode;
  api: OnboardingApi;                 // injected — wizard never calls getOnboardingApi() directly
  onComplete?: () => Promise<void>;   // only invoked at terminal CTA in live mode
}
```

### Live vs demo behaviour matrix

| Behaviour | `mode="live"` | `mode="demo"` |
|---|---|---|
| `OnboardingApi` adapter | Caller passes `getOnboardingApi()` (env flag decides Mock vs Http). | Caller passes `new MockOnboardingApi()` — forced, ignores the build flag. |
| `onComplete` callback at terminal CTA | Caller passes `completeV2Onboarding` server action. Awaited; on success → `router.push("/brand/dashboard")`. On failure → `completeError` shown inline (preserved from current live UX). | Caller passes nothing. Wizard treats it as undefined and runs `restart()` instead. No server action, no router push, no `completeError` path reachable. |
| Storage rehydrate on mount | Already removed from the live page — wizard preserves that (no rehydrate). | Same — no rehydrate. |
| Storage writes (skipAll, launchDone) | Writes `"complete"` to `localStorage["cortex.onboarding.v2"]` (vestigial — never read; preserved to match current live behaviour exactly). | No-op. State dies with the tab. |
| Topbar "Demo" pill | Hidden. | Renders on steps 0–5 (TopBar prop) and step 7 (inline `<Badge color="ink">`). Step 6 has no chrome. |
| Topbar language-toggle target | `/onboarding/v2` ↔ `/onboarding/v2/zh-TW` | `/demo/onboarding` ↔ `/demo/onboarding/zh-TW` |

### Concentration of mode branches

To keep `mode === "demo"` checks at the top of `wizard.tsx` instead of scattered through the body, the wizard interprets the mode once into a small `storage` helper, a `langSwitchHref` constant, and a `handleEnterDiscover` callback. The body's call sites stay structurally identical:

```ts
const storage = mode === "live"
  ? {
      write: (v: string) => { try { localStorage.setItem(STORAGE_KEY, v); } catch {} },
    }
  : { write: () => {} };

const langSwitchHref = (mode === "demo"
  ? "/demo/onboarding/zh-TW"      // en wizard ↔ zh wizard
  : "/onboarding/v2/zh-TW") as Route;

const handleEnterDiscover = useCallback(async () => {
  if (mode === "demo" || !onComplete) {
    restart();
    return;
  }
  try {
    await onComplete();
  } catch (e) {
    setCompleteError(e instanceof Error ? e.message : "Couldn't finish onboarding. Try again.");
    return;
  }
  router.push("/brand/dashboard");
}, [mode, onComplete, restart, router]);
```

The wizard preserves **everything else** from the current live page: the `loadModeled` mount effect (instant local-constant fetch), the `runAnalyze` user-triggered flow (with the three isolated void-async fetches for media / questions / voice tones), the `loadStatus` error gate, the `completeError` inline alert. The lift is faithful — only the four prop-driven divergences above change.

### Why the inversion (mode + DI) instead of pure DI

A purist would argue: if `api` and `onComplete` cover the API and server-action divergences, and `langSwitchHref` could be a prop too, why keep a `mode` discriminant at all? Two reasons:

1. The "Demo" pill (Section 6) is a *UI fact* that the wizard renders inline (on step 7's slim topbar). Naming it `showDemoBadge` would work, but `mode` reads more honestly: this wizard knows whether it's the live or demo flow because three things change at once (api source, completion semantics, visual signal).
2. Storage writes are an audit-trail concern that would otherwise be a fourth prop. Folding them into `mode` keeps the wizard's surface to three props.

## 6. The Demo pill

**Placement.** Inside each language's `<TopBar>` primitive, immediately right of the Cortex `C` logo. Renders on steps 0–5 (rail topbar) and step 7 (slim "Brand Agent online" topbar). Hidden on step 6 (launch overlay covers the chrome).

**Visual.** Soft and ignorable — must not distract from a live demo. Reuses the existing `<Badge>` primitive with palette-appropriate colours: `<Badge color="onDark">` on the dark teal-gradient rail topbar (steps 0–5), `<Badge color="ink">` on the white step 7 inline topbar. The `<Badge>` primitive already has the right typography (`font-size: 10`, `font-weight: 700`, `letter-spacing: 0.06em`, uppercase, `padding: 3px 8px`, `border-radius: 3`); no new component.

**Copy.** The string is `Demo` in both locales — untranslated. "Demo" is loanword-stable in Traditional Chinese product UI; translating to `示範` or `展示版` would be more ambiguous than the English word.

**Wiring.** `<TopBar>` already gained `showDemoBadge?: boolean` and `langSwitchHref?: Route` props in Tasks 1 and 2 of the plan. The wizard passes `showDemoBadge={mode === "demo"}` and the computed `langSwitchHref` to `<TopBar>` for steps 0–5. The step 7 inline topbar (rendered directly in the wizard body, not via the `<TopBar>` primitive) gets an inline `{mode === "demo" ? <Badge color="ink">Demo</Badge> : null}`. The pill component itself is not extracted — three lines of JSX in two locations is cheaper than a shared component that breaks the existing independence of `components/onboarding-v2/` and `components/onboarding-v2-zh/`.

## 7. i18n & copy

The wizard body copy is identical between live and demo. Step components, rail labels, button copy, the URL placeholder (`acmebank.asia`), the seeded brand name, the terminal CTA label, all empty states — reused verbatim. The terminal CTA on the "Brand Agent online" screen says `Enter Discover` / `進入 Discover` in both modes; only its click handler changes (live: `router.push("/brand/dashboard")`; demo: `restart()`). The wizard owns the handler; the step component is untouched.

Two copy points are new in demo:

1. **Demo pill** — string `Demo`, untranslated in both locales (Section 6).

2. **Browser tab title** for the demo pages.
   - Live: existing default (no `metadata` export on the live page; preserved as-is).
   - Demo (en): `Cortex · Demo` — via `export const metadata = { title: "Cortex · Demo" }` on `app/demo/onboarding/page.tsx` (the server-component wrapper).
   - Demo (zh): `Cortex · 體驗版` — via the same export on `app/demo/onboarding/zh-TW/page.tsx`.

No i18n framework is introduced. Cortex's existing en/zh-TW split is by route, not by a runtime locale switcher, and the demo follows the same convention.

## 8. Error handling

The flow is API-driven through the injected `OnboardingApi`. Realistic failure modes:

- **`analyzeBrand()` rejects** (live mode under `HttpOnboardingApi`, ~25s LLM extraction can fail). The wizard surfaces a full-screen `loadStatus === "error"` retry screen. Preserved verbatim from the current live page. In demo mode the Mock adapter never rejects (it returns local constants), so this code path is dead but harmless.
- **`completeV2Onboarding()` throws** (live mode only — server-action auth or brand-context check fails). The wizard catches it and renders an inline alert with the thrown message, suppressing the `router.push`. Preserved from current live page. In demo mode `onComplete` is undefined, so this code path is dead; demo's terminal CTA always restarts.
- **Per-dataset fetches in `runAnalyze` (`getMediaNetwork`, `getLiveQuestions`, `getVoiceTones`) reject.** Each is wrapped in its own isolated `void (async () => { try {...} catch {...} })()` block in the existing live code — preserved. A media/questions/voice failure is non-fatal: the corresponding step shows an empty state. Demo mode's Mock adapter never rejects.
- **`localStorage` unavailable (privacy-mode browser).** The wizard's storage helper wraps writes in `try / catch`. Demo mode's storage helper is a no-op, so it's trivially safe.

There is no demo-specific error path. The demo route shares every error-handling structure with the live route — the only difference is the underlying adapter never throws.

## 9. Testing

Three focused test files plus zh-TW siblings, all colocated under `<area>/__tests__/*.test.tsx` per Cortex convention. All tests construct a hand-rolled fake `OnboardingApi` (with `vi.fn()` spies) and pass it directly to the wizard as the `api` prop — no global `vi.mock` of `getOnboardingApi` is needed, because the wizard never calls the factory itself. This is meaningfully cleaner than the existing `page-load-states.test.tsx`, which has to `vi.mock("@/lib/onboarding/api", ...)` because the current page is tightly coupled to the global factory. DI improves testability as a side-effect.

The test rig already mocks `next/navigation` and `next-auth/react` globally in `web/tests/setup.ts`; `router.push` is therefore a `vi.fn()` we can assert on. The existing convention uses `fireEvent` from `@testing-library/react` for click interactions — **no new dependency** (`@testing-library/user-event`) is needed.

**1. `components/onboarding-v2/__tests__/wizard.live.test.tsx` (+ zh sibling)** — regression net for the lift.

The most important test in the feature. Catches any behaviour change the refactor introduces to the production onboarding for signed-in users.

- Step 0 renders on mount (the URL-entry screen, with the `Analyze my brand` button visible).
- Clicking `Set up later` fires; `mode === "live"` writes `"complete"` to `localStorage["cortex.onboarding.v2"]`.
- A successful drive through to step 7 with the `Enter Discover` CTA invokes the injected `onComplete` spy once, then calls `router.push("/brand/dashboard")` exactly once.
- A failing `onComplete` (spy throws) suppresses `router.push` and renders an inline error alert.
- No "Demo" pill renders anywhere.

**2. `components/onboarding-v2/__tests__/wizard.demo.test.tsx` (+ zh sibling)** — new behaviour.

- Pre-set `localStorage["cortex.onboarding.v2"] = "complete"` before render → wizard still renders step 0 (the wizard does not rehydrate; this preserves the live page's existing behaviour, and the demo confirms the same).
- Clicking `Set up later` in demo mode does NOT write to `localStorage["cortex.onboarding.v2"]`.
- Drive to step 7, click the terminal CTA → `router.push` is NOT called, the wizard returns to step 0, and the injected `onComplete` (absent in demo) is never invoked.
- The "Demo" pill renders on the rail topbar (step 0).

**3. `app/demo/onboarding/__tests__/page.test.tsx` (+ zh sibling)** — smoke test.

Renders the demo `page.tsx` (the server-component wrapper) with the client child mocked, asserts the `metadata` export has the right `title`. A second test renders the `client.tsx` with `<OnboardingV2Wizard>` mocked and verifies it was called with `mode="demo"` and an API instance that is `instanceof MockOnboardingApi`. Exists so a future accidental flip (e.g., dropping `mode="demo"` or swapping in `getOnboardingApi()`) fails CI immediately.

**Test-rig pre-paid constraints.**

The wizard imports nothing from `cortex-api.ts`, `http-api`, `analyze-actions`, `media-actions`, or `complete-actions` — those are caller concerns (the live page imports them and threads them into the wizard's props). Per the established Cortex test convention, any of those would pull in real next-auth + `next/server`, which Vite's Vitest resolver can't handle and which fails collection. The shared wizard MUST remain free of these imports for tests to load.

**Explicitly not tested.**
- Individual `step-*.tsx` components — unchanged by this feature.
- Visual styling of the Demo pill — assertion that the element with text `"Demo"` exists is enough.
- E2E browser flows — manual walkthrough is the acceptance bar.

## 10. Rollout

Single PR off `develop` containing:
- The `wizard.tsx` extraction for both languages (with `api` and `onComplete` props).
- The two live `page.tsx` updates (rewired to `useMemo(getOnboardingApi)` + `<Wizard onComplete>`).
- The four new demo route files (server `page.tsx` + client `client.tsx` per language).
- The `primitives.tsx` topbar prop additions (already shipped in Tasks 1 and 2).
- All test files from Section 9.

Manual smoke: open `/demo/onboarding` and `/demo/onboarding/zh-TW` in incognito (no session), drive the wizard end to end, confirm the terminal CTA restarts to step 0, confirm reload after completion still lands at step 0, confirm the Demo pill renders.

No migration, no feature flag, no follow-up infra PR. The route appears the moment the PR merges.

## 11. Risks & open questions

**Risks.**

- *The lift breaks live onboarding.* Mitigated by the `wizard.live.test.tsx` regression net (Section 9, test #1). Highest-priority test in the feature.
- *Search engines index `/demo/onboarding`.* No `robots.txt` change is in scope. If GTM ever wants the URL not indexed, follow up by adding `Disallow: /demo/` and/or a `<meta name="robots" content="noindex">` tag on the demo pages. Out of scope today (link-only sales use; low immediate risk).
- *The "Demo" pill is too subtle and a viewer assumes it's the real product.* Acceptable — the live demo is delivered by a human who frames the context. The pill is for screenshots, not for unattended visitors.

**Open questions: none.** All Section 3 decisions are locked.
