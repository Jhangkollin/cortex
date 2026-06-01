# Onboarding v2 Demo Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a public, auth-free clone of the `/onboarding/v2` wizard at `/demo/onboarding` (en) and `/demo/onboarding/zh-TW` (zh), driven entirely by the existing mock data, for GTM and CEO live demos.

**Architecture:** Extract the wizard body from the two existing page components into shared client components `<OnboardingV2Wizard mode>` and `<OnboardingV2WizardZh mode>`. The `mode: "live" | "demo"` prop controls three things: localStorage rehydrate/writes (live: yes; demo: no-op), the terminal CTA handler (live: `router.push("/brand/dashboard")`; demo: `restart()`), and a soft "Demo" pill in the topbar. Step components, mock data, and copy are unchanged.

**Tech Stack:** Next.js 16 App Router, React client components, TypeScript, Vitest + Testing Library (jsdom). Existing `next/navigation` and `next-auth/react` are globally mocked in `web/tests/setup.ts`.

**Spec reference:** `docs/superpowers/specs/2026-05-20-onboarding-v2-demo-mode-design.md`

---

## Plan revision note

**Revised 2026-05-20** after Tasks 1 and 2 shipped successfully. Tasks 3+ have been **rewritten** to match the actual shape of `/onboarding/v2/page.tsx` on `develop` (599 lines, API-driven through the `OnboardingApi` seam, post-SP-3a/SP-media/SP-questions/SP-voice). The original Task 3+ assumed a mock-only page that no longer exists on develop. See `docs/superpowers/specs/2026-05-20-onboarding-v2-demo-mode-design.md` (revised the same day) for the corresponding spec amendments.

Tasks 1 and 2 are unchanged and **already shipped** (commits `1059460`, `a460fc1`, `bd19451`).

**Mid-execution amendment (Tasks 3 + 4):** Both wizards adopted a `brand ?? EXTRACTED_BRAND` fallback at the step-7 `<StepComplete>` invocation, replacing the original `{step === 7 && brand ? ...}` guard. The original page had a latent edge case where clicking "Set up later" at step 0 jumped to step 7 with `brand === null`, suppressing `<StepComplete>` rendering. The fallback closes that gap (so step 7 always shows useful content) and is consistent across the en and zh wizards. This deviation was applied in commits `055d41b` (zh) and `e8a2c07` (en).

## File map (revised)

**Modify (4 files):**
- `web/src/components/onboarding-v2/primitives.tsx` — `<TopBar>` gains `showDemoBadge?: boolean` and `langSwitchHref?: Route` props (already shipped in Task 1).
- `web/src/components/onboarding-v2-zh/primitives.tsx` — same prop additions (already shipped in Task 2).
- `web/src/app/(auth)/onboarding/v2/page.tsx` — slim to wire `useMemo(() => getOnboardingApi(), [])` into `<OnboardingV2Wizard mode="live" api onComplete={completeV2Onboarding} />`.
- `web/src/app/(auth)/onboarding/v2/zh-TW/page.tsx` — same shape, zh sibling.

**Create (12 files):**
- `web/src/components/onboarding-v2/wizard.tsx` — shared client component, props `{ mode, api, onComplete? }`.
- `web/src/components/onboarding-v2-zh/wizard.tsx` — zh sibling, same prop surface.
- `web/src/app/demo/onboarding/page.tsx` — **server component** exporting `metadata`, renders `<DemoOnboardingClient />`.
- `web/src/app/demo/onboarding/client.tsx` — **client component** wiring `useMemo(() => new MockOnboardingApi(), [])` into `<OnboardingV2Wizard mode="demo" api />`.
- `web/src/app/demo/onboarding/zh-TW/page.tsx` — zh demo server wrapper.
- `web/src/app/demo/onboarding/zh-TW/client.tsx` — zh demo client wrapper.
- `web/src/components/onboarding-v2/__tests__/wizard.live.test.tsx` — regression net for the en lift.
- `web/src/components/onboarding-v2/__tests__/wizard.demo.test.tsx` — en demo behaviour.
- `web/src/components/onboarding-v2-zh/__tests__/wizard.live.test.tsx` — zh regression net.
- `web/src/components/onboarding-v2-zh/__tests__/wizard.demo.test.tsx` — zh demo behaviour.
- `web/src/app/demo/onboarding/__tests__/page.test.tsx` — en demo route smoke test (covers both server `page.tsx` metadata and client `client.tsx` wiring).
- `web/src/app/demo/onboarding/zh-TW/__tests__/page.test.tsx` — zh demo route smoke test.

---

## Task 1: Add `showDemoBadge` + `langSwitchHref` props to en `<TopBar>`

**Files:**
- Modify: `web/src/components/onboarding-v2/primitives.tsx`

- [ ] **Step 1: Modify the `<LangSwitch>` component to accept an explicit target href**

Replace the `LangSwitch` component (currently spanning roughly lines 354–399 of `primitives.tsx`) with:

```tsx
function LangSwitch({
  current,
  targetHref,
}: {
  current: "en" | "zh";
  targetHref: Route;
}) {
  const isEn = current === "en";
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        fontSize: 11,
        fontFamily: "var(--font-mono)",
        color: "rgba(255,255,255,0.5)",
        padding: "5px 10px",
        border: "1px solid rgba(255,255,255,0.18)",
        borderRadius: 999,
      }}
    >
      <span style={{ color: "#fff", fontWeight: 700 }}>{isEn ? "EN" : "繁中"}</span>
      <span aria-hidden style={{ color: "rgba(255,255,255,0.3)" }}>|</span>
      <Link
        href={targetHref}
        style={{
          color: "rgba(255,255,255,0.7)",
          textDecoration: "none",
          fontWeight: 500,
        }}
      >
        {isEn ? "繁中" : "EN"}
      </Link>
    </span>
  );
}
```

- [ ] **Step 2: Modify the `<TopBar>` component to thread the two new props through**

Replace the `<TopBar>` props and the `<LangSwitch>` invocation. The signature and the `<LangSwitch>` line are the only changes — everything else in `<TopBar>` stays as-is.

Find the existing `<TopBar>` props (currently `railStep`, `steps`, `onSkip`, `onExit`, `lang = "en"`) and replace with:

```tsx
export function TopBar({
  railStep,
  steps,
  onSkip,
  onExit,
  lang = "en",
  showDemoBadge = false,
  langSwitchHref = "/onboarding/v2/zh-TW" as Route,
}: {
  railStep: RailIndex;
  steps: readonly string[];
  onSkip: () => void;
  onExit: () => void;
  lang?: "en" | "zh";
  showDemoBadge?: boolean;
  langSwitchHref?: Route;
}) {
```

Find the `<LangSwitch current={lang} />` line inside `<TopBar>` (currently around line 499) and replace with:

```tsx
<LangSwitch current={lang} targetHref={langSwitchHref} />
```

- [ ] **Step 3: Render the Demo badge next to the Cortex `C` block when `showDemoBadge` is true**

Inside `<TopBar>`, immediately after the closing `</span>` of the "Welcome to Cortex" label block (the inner span that contains "Brand setup · First-time"), insert the badge before the outer button's closing `</button>`. Concretely, find this section:

```tsx
            <span
              style={{
                fontSize: 11,
                color: "rgba(255,255,255,0.6)",
                marginTop: 2,
                display: "block",
              }}
            >
              Brand setup · First-time
            </span>
          </span>
        </button>
```

Replace with (the only addition is the `{showDemoBadge ? ... : null}` block between `</span>` and `</button>`):

```tsx
            <span
              style={{
                fontSize: 11,
                color: "rgba(255,255,255,0.6)",
                marginTop: 2,
                display: "block",
              }}
            >
              Brand setup · First-time
            </span>
          </span>
          {showDemoBadge ? <Badge color="onDark" style={{ marginLeft: 10 }}>Demo</Badge> : null}
        </button>
```

`<Badge>` is already exported from this file, so no new import is needed.

- [ ] **Step 4: Run typecheck**

Run from `web/`: `npm run type-check`
Expected: PASS. The new optional props default to working values, so the existing live page (which passes none of them) still compiles.

- [ ] **Step 5: Commit**

```bash
git add web/src/components/onboarding-v2/primitives.tsx
git commit -m "feat(onboarding-v2): TopBar accepts showDemoBadge + langSwitchHref"
```

---

## Task 2: Mirror Task 1 changes in zh `<TopBar>`

**Files:**
- Modify: `web/src/components/onboarding-v2-zh/primitives.tsx`

The zh primitives are described in their file header as "byte-for-byte identical [to the en sibling] except for translated TopBar copy and a flipped LangSwitch target." Apply the same edits as Task 1, with two adjustments:

- The default `langSwitchHref` is `"/onboarding/v2" as Route` (zh's "other side" is en).
- The Badge `Demo` string is unchanged — Section 6 of the spec keeps "Demo" untranslated in both locales.

- [ ] **Step 1: Modify the zh `<LangSwitch>` component**

Same code as Task 1 Step 1 — paste it into `web/src/components/onboarding-v2-zh/primitives.tsx`, replacing the existing `LangSwitch` (currently spanning roughly lines 348–394 of that file).

- [ ] **Step 2: Modify the zh `<TopBar>` props**

Same shape as Task 1 Step 2, with the zh defaults:

```tsx
export function TopBar({
  railStep,
  steps,
  onSkip,
  onExit,
  lang = "zh",
  showDemoBadge = false,
  langSwitchHref = "/onboarding/v2" as Route,
}: {
  railStep: RailIndex;
  steps: readonly string[];
  onSkip: () => void;
  onExit: () => void;
  lang?: "en" | "zh";
  showDemoBadge?: boolean;
  langSwitchHref?: Route;
}) {
```

Replace `<LangSwitch current={lang} />` with `<LangSwitch current={lang} targetHref={langSwitchHref} />` inside the zh `<TopBar>` body (currently around line 494).

- [ ] **Step 3: Render the Demo badge in the zh TopBar**

Find the closing of the zh "歡迎使用 Cortex" label block (the inner span containing "Brand setup · 第一次進入") and insert the badge in the same position as Task 1 Step 3:

```tsx
            <span
              style={{
                fontSize: 11,
                color: "rgba(255,255,255,0.6)",
                marginTop: 2,
                display: "block",
              }}
            >
              Brand setup · 第一次進入
            </span>
          </span>
          {showDemoBadge ? <Badge color="onDark" style={{ marginLeft: 10 }}>Demo</Badge> : null}
        </button>
```

- [ ] **Step 4: Run typecheck**

Run from `web/`: `npm run type-check`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/src/components/onboarding-v2-zh/primitives.tsx
git commit -m "feat(onboarding-v2-zh): TopBar accepts showDemoBadge + langSwitchHref"
```

---

## Task 3: Extract en wizard + live regression tests (TDD)

> **Parallelizable with Task 4** — completely disjoint file sets. May be dispatched concurrently.

**Files:**
- Create: `web/src/components/onboarding-v2/wizard.tsx` (lifted from the current `(auth)/onboarding/v2/page.tsx` with specific edits)
- Create: `web/src/components/onboarding-v2/__tests__/wizard.live.test.tsx`
- Modify: `web/src/app/(auth)/onboarding/v2/page.tsx`

**Approach.** The current `(auth)/onboarding/v2/page.tsx` is 599 lines. The lift is faithful — copy the file into `components/onboarding-v2/wizard.tsx`, then apply a small set of targeted edits to introduce the `mode` / `api` / `onComplete` prop surface. Then slim the en page down to a thin client wrapper that wires `getOnboardingApi()` + `completeV2Onboarding` into the new component.

- [ ] **Step 1: Write the live regression test**

Create `web/src/components/onboarding-v2/__tests__/wizard.live.test.tsx`:

```tsx
/**
 * Regression net for the live-mode wizard after the lift from
 * /onboarding/v2/page.tsx into the shared <OnboardingV2Wizard> component.
 *
 * Uses fireEvent (the existing repo convention — see page-load-states.test.tsx)
 * and a hand-rolled OnboardingApi fake with vi.fn() spies. No global mocking
 * of getOnboardingApi() needed because the wizard now takes the api as a prop.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  CRAWL_TASKS,
  DEPLOY_AGENTS,
  DEPLOY_LOG,
  EXTRACTED_BRAND,
  LIVE_QUESTIONS,
  MEDIA_NETWORK,
  VOICE_TONES,
} from "@/components/onboarding-v2/data";
import { OnboardingV2Wizard } from "@/components/onboarding-v2/wizard";
import type { OnboardingApi } from "@/lib/onboarding/api";
import { router } from "@tests/helpers/session-mock-state";

function makeOkApi(): OnboardingApi {
  return {
    analyzeBrand: vi.fn(async () => EXTRACTED_BRAND),
    getCrawlTasks: vi.fn(async () => CRAWL_TASKS),
    getMediaNetwork: vi.fn(async () => MEDIA_NETWORK),
    getLiveQuestions: vi.fn(async () => LIVE_QUESTIONS),
    getVoiceTones: vi.fn(async () => VOICE_TONES),
    getDeployAgents: vi.fn(async () => DEPLOY_AGENTS),
    getDeployLog: vi.fn(async () => DEPLOY_LOG),
  };
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("OnboardingV2Wizard — mode='live'", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("renders step 0 (URL entry) on mount", async () => {
    const api = makeOkApi();
    const onComplete = vi.fn(async () => {});
    render(<OnboardingV2Wizard mode="live" api={api} onComplete={onComplete} />);

    expect(
      await screen.findByRole("button", { name: /analyze my brand/i }),
    ).toBeInTheDocument();
  });

  it("does not render the Demo badge in live mode", () => {
    const api = makeOkApi();
    const onComplete = vi.fn(async () => {});
    render(<OnboardingV2Wizard mode="live" api={api} onComplete={onComplete} />);

    expect(screen.queryByText("Demo")).not.toBeInTheDocument();
  });

  it("Set up later writes the completion flag to localStorage", () => {
    const api = makeOkApi();
    const onComplete = vi.fn(async () => {});
    render(<OnboardingV2Wizard mode="live" api={api} onComplete={onComplete} />);

    fireEvent.click(screen.getByRole("button", { name: /set up later/i }));
    expect(window.localStorage.getItem("cortex.onboarding.v2")).toBe("complete");
  });

  it("Enter Discover (via Set up later → step 7) calls onComplete once then router.push(/brand/dashboard)", async () => {
    const api = makeOkApi();
    const onComplete = vi.fn(async () => {});
    render(<OnboardingV2Wizard mode="live" api={api} onComplete={onComplete} />);

    // Skip-to-end shortcut: Set up later jumps directly to step 7.
    fireEvent.click(screen.getByRole("button", { name: /set up later/i }));
    const enterDiscover = await screen.findByRole("button", {
      name: /enter discover/i,
    });
    fireEvent.click(enterDiscover);

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalledTimes(1);
      expect(router.push).toHaveBeenCalledWith("/brand/dashboard");
    });
  });

  it("Enter Discover with a failing onComplete surfaces the error inline and suppresses router.push", async () => {
    const api = makeOkApi();
    const onComplete = vi.fn(async () => {
      throw new Error("server action boom");
    });
    render(<OnboardingV2Wizard mode="live" api={api} onComplete={onComplete} />);

    fireEvent.click(screen.getByRole("button", { name: /set up later/i }));
    const enterDiscover = await screen.findByRole("button", {
      name: /enter discover/i,
    });
    fireEvent.click(enterDiscover);

    expect(await screen.findByRole("alert")).toHaveTextContent(/server action boom/i);
    expect(router.push).not.toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

From `/Users/okis.chuang/Documents/dev/cortex/.claude/worktrees/onboarding-v2-demo-spec/web/`:

```
npm test -- src/components/onboarding-v2/__tests__/wizard.live.test.tsx
```

Expected: FAIL with `Failed to resolve import "@/components/onboarding-v2/wizard"`.

- [ ] **Step 3: Create wizard.tsx by copy + edit from the existing page**

The wizard is the existing page body, faithfully preserved, with a precise set of edits to introduce the `mode` / `api` / `onComplete` prop surface and the Demo pill. Start with a `cp`:

```
cp web/src/app/\(auth\)/onboarding/v2/page.tsx web/src/components/onboarding-v2/wizard.tsx
```

Then apply these edits to `web/src/components/onboarding-v2/wizard.tsx` in order:

**Edit 3.1 — imports.** Replace the import block at the top of the file (the `import` lines starting around line 21 and ending around line 45) with:

```tsx
import type { Route } from "next";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import type {
  CrawlTask,
  DeployAgent,
  DeployLogLine,
  ExtractedBrand,
  LiveQuestion,
  Media,
  VoiceTone,
} from "@/components/onboarding-v2/data";
import { RAIL_STEPS, type InternalStep, railFor } from "@/components/onboarding-v2/data";
import { LaunchOverlay } from "@/components/onboarding-v2/launch-overlay";
import { Badge, Icon, OnbButton, TopBar } from "@/components/onboarding-v2/primitives";
import { StepComplete } from "@/components/onboarding-v2/step-complete";
import { StepCrawl } from "@/components/onboarding-v2/step-crawl";
import { StepLaunch } from "@/components/onboarding-v2/step-launch";
import { StepMedia } from "@/components/onboarding-v2/step-media";
import { StepQuestions } from "@/components/onboarding-v2/step-questions";
import { StepReview } from "@/components/onboarding-v2/step-review";
import { StepWelcome } from "@/components/onboarding-v2/step-welcome";
import type { OnboardingApi } from "@/lib/onboarding/api";
```

Changes from the original imports: dropped `completeV2Onboarding` and `getOnboardingApi` (now injected via props); added `Badge` (for the step 7 Demo pill), `Route` (for `langSwitchHref`), and the `OnboardingApi` type.

**Edit 3.2 — module docstring.** Replace the existing docstring above `const STORAGE_KEY` with:

```tsx
/**
 * Brand onboarding v2 wizard — shared between the live route
 * (/onboarding/v2) and the public demo route (/demo/onboarding).
 *
 * `mode="live"` is the production flow: writes a vestigial completion flag
 * to localStorage (current behaviour preserved), threads through to the
 * caller-supplied `completeV2Onboarding` server action on Enter Discover,
 * and falls through to /brand/dashboard on success.
 *
 * `mode="demo"` is the public, auth-free clone: localStorage writes become
 * no-ops, `onComplete` is intentionally omitted, and Enter Discover
 * restarts the wizard so the next demo viewer sees step 0.
 *
 * All wizard data continues to flow through the OnboardingApi seam —
 * the live caller passes `getOnboardingApi()`, the demo caller passes
 * `new MockOnboardingApi()` directly.
 */
```

**Edit 3.3 — add WizardMode type just below STORAGE_KEY.** Right after the `const INITIAL_URL = "acmebank.asia";` line (which immediately follows `STORAGE_KEY`), insert:

```tsx
export type WizardMode = "live" | "demo";
```

**Edit 3.4 — function signature.** Find the function declaration line:

```tsx
export default function OnboardingV2Page() {
```

Replace with (note: no `default`, no `()` — explicit named export, props destructured):

```tsx
export function OnboardingV2Wizard({
  mode,
  api,
  onComplete,
}: {
  mode: WizardMode;
  api: OnboardingApi;
  onComplete?: () => Promise<void>;
}) {
```

**Edit 3.5 — drop the two `const api = getOnboardingApi();` calls.** They appear inside `loadModeled` and `runAnalyze`. Delete those two lines entirely — both callbacks now reference the `api` prop directly. The lines look exactly like:

```tsx
    const api = getOnboardingApi();
```

Each of those two lines is followed by `try {` — leave the rest of those callbacks unchanged.

Also add `api` to the dependency arrays of `loadModeled` and `runAnalyze`. Find:

```tsx
  const loadModeled = useCallback(async () => {
```

…and `useCallback(async () => {` for `runAnalyze`. Their closing `}, [])` lines should become `}, [api])`.

**Edit 3.6 — skipAll, launchDone, restart: gate localStorage writes on mode.**

Find `const skipAll = useCallback(() => {` block. The original body is:

```tsx
  const skipAll = useCallback(() => {
    try {
      localStorage.setItem(STORAGE_KEY, "complete");
    } catch {
      // ignore
    }
    setStep(7);
  }, []);
```

Replace with:

```tsx
  const skipAll = useCallback(() => {
    if (mode === "live") {
      try {
        localStorage.setItem(STORAGE_KEY, "complete");
      } catch {
        // ignore — privacy-mode browsers; non-fatal
      }
    }
    setStep(7);
  }, [mode]);
```

Find `const launchDone = useCallback(() => {` block. Same shape — wrap the `localStorage.setItem` in `if (mode === "live")` and add `mode` to the deps array (currently `[]`).

Find `const restart = useCallback(() => {` block. The original starts with a `try { localStorage.removeItem(STORAGE_KEY); } catch {}`. Wrap that in `if (mode === "live")` and add `mode` to the deps array.

**Edit 3.7 — handleEnterDiscover.** Find:

```tsx
  const handleEnterDiscover = useCallback(async () => {
    try {
      await completeV2Onboarding();
    } catch (e) {
      setCompleteError(
        e instanceof Error ? e.message : "Couldn't finish onboarding. Try again.",
      );
      return;
    }
    router.push("/brand/dashboard");
  }, [router]);
```

Replace with:

```tsx
  const handleEnterDiscover = useCallback(async () => {
    if (mode === "demo" || !onComplete) {
      // Demo mode (no server action wired). Restart so the next viewer sees
      // step 0 instead of being stuck on the success screen.
      restart();
      return;
    }
    try {
      await onComplete();
    } catch (e) {
      setCompleteError(
        e instanceof Error ? e.message : "Couldn't finish onboarding. Try again.",
      );
      return;
    }
    router.push("/brand/dashboard");
  }, [mode, onComplete, restart, router]);
```

**Edit 3.8 — compute langSwitchHref + pass new props to TopBar.** Just before the `return (` of the component (right after `handleEnterDiscover` declaration), add:

```tsx
  const langSwitchHref = (mode === "demo"
    ? "/demo/onboarding/zh-TW"
    : "/onboarding/v2/zh-TW") as Route;
```

Find the `<TopBar` invocation (inside the `{step <= 5 ? (` block). The original is:

```tsx
      {step <= 5 ? (
        <TopBar railStep={railStep} steps={RAIL_STEPS} onSkip={skipAll} onExit={restart} />
      ) : step === 6 ? null : (
```

Replace with:

```tsx
      {step <= 5 ? (
        <TopBar
          railStep={railStep}
          steps={RAIL_STEPS}
          onSkip={skipAll}
          onExit={restart}
          showDemoBadge={mode === "demo"}
          langSwitchHref={langSwitchHref}
        />
      ) : step === 6 ? null : (
```

**Edit 3.9 — inline Demo pill on step 7's slim topbar.** Inside the step-7 inline topbar block (the one that starts with `{ background: "#fff", borderBottom: ... }`), find the `C` logo div:

```tsx
              <div
                style={{
                  width: 30,
                  height: 30,
                  borderRadius: 6,
                  background: "var(--mly-teal-800)",
                  color: "#fff",
                  display: "grid",
                  placeItems: "center",
                  fontWeight: 700,
                }}
              >
                C
              </div>
              <div>
```

Insert the Badge between `</div>` and `<div>`:

```tsx
              <div
                style={{
                  width: 30,
                  height: 30,
                  borderRadius: 6,
                  background: "var(--mly-teal-800)",
                  color: "#fff",
                  display: "grid",
                  placeItems: "center",
                  fontWeight: 700,
                }}
              >
                C
              </div>
              {mode === "demo" ? <Badge color="ink">Demo</Badge> : null}
              <div>
```

That completes the wizard.tsx edits.

- [ ] **Step 4: Slim the live en page**

Replace the entire contents of `web/src/app/(auth)/onboarding/v2/page.tsx` with:

```tsx
"use client";

import { useMemo } from "react";

import { completeV2Onboarding } from "@/app/(auth)/onboarding/v2/complete-actions";
import { OnboardingV2Wizard } from "@/components/onboarding-v2/wizard";
import { getOnboardingApi } from "@/lib/onboarding/api";

export default function OnboardingV2Page() {
  // useMemo so the api instance is stable across re-renders. The factory
  // returns a fresh class instance each call; the wizard's deps arrays
  // expect a stable reference.
  const api = useMemo(() => getOnboardingApi(), []);
  return (
    <OnboardingV2Wizard
      mode="live"
      api={api}
      onComplete={completeV2Onboarding}
    />
  );
}
```

- [ ] **Step 5: Run the live regression tests**

From `web/`:

```
npm test -- src/components/onboarding-v2/__tests__/wizard.live.test.tsx
```

Expected: all 5 tests PASS.

- [ ] **Step 6: Run typecheck**

From `web/`: `npm run type-check`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add web/src/components/onboarding-v2/wizard.tsx web/src/components/onboarding-v2/__tests__/wizard.live.test.tsx "web/src/app/(auth)/onboarding/v2/page.tsx"
git commit -m "refactor(onboarding-v2): extract wizard into shared client component"
```

If the commit fails with `index.lock` (because the parallel Task 4 commit is racing), wait one second and retry the same `git commit` invocation.

---

## Task 4: Extract zh wizard + live regression tests (TDD)

> **Parallelizable with Task 3** — completely disjoint file sets. May be dispatched concurrently.

**Files:**
- Create: `web/src/components/onboarding-v2-zh/wizard.tsx`
- Create: `web/src/components/onboarding-v2-zh/__tests__/wizard.live.test.tsx`
- Modify: `web/src/app/(auth)/onboarding/v2/zh-TW/page.tsx`

Mirror of Task 3 in the zh-TW sibling. The current `(auth)/onboarding/v2/zh-TW/page.tsx` is 574 lines, structurally parallel to the en page (same state machine, same OnboardingApi seam, same completeV2Onboarding server action, different copy).

- [ ] **Step 1: Write the zh live regression test**

Create `web/src/components/onboarding-v2-zh/__tests__/wizard.live.test.tsx` with the same shape as Task 3 Step 1, with these substitutions:

- Import path: `@/components/onboarding-v2-zh/data` instead of `@/components/onboarding-v2/data`.
- Import path: `@/components/onboarding-v2-zh/wizard` instead of `@/components/onboarding-v2/wizard`.
- Component name: `OnboardingV2WizardZh` instead of `OnboardingV2Wizard`.
- Button text selectors using zh copy:
  - `稍後再設定` instead of `set up later`.
  - `分析我的品牌` instead of `analyze my brand`. (Confirm via grep of `step-welcome.tsx` in the zh tree if needed.)
  - `進入 Discover` instead of `enter discover`.
- Everything else (the `makeOkApi` helper, the `vi.fn()` spies, the `router.push` assertions, the `vi.restoreAllMocks` in `afterEach`) is identical.

If a button label in the zh wizard differs from what you expect, grep the actual zh step component file (`web/src/components/onboarding-v2-zh/step-*.tsx`) and use the actual label.

- [ ] **Step 2: Run the test to verify it fails**

From `web/`: `npm test -- src/components/onboarding-v2-zh/__tests__/wizard.live.test.tsx`
Expected: FAIL with `Failed to resolve import "@/components/onboarding-v2-zh/wizard"`.

- [ ] **Step 3: Create the zh wizard component via copy + edit**

```
cp "web/src/app/(auth)/onboarding/v2/zh-TW/page.tsx" web/src/components/onboarding-v2-zh/wizard.tsx
```

Apply the same 9 edits as Task 3 Step 3 (3.1 through 3.9) with these adjustments:

- **Edit 4.1 (imports):** All `@/components/onboarding-v2/...` paths become `@/components/onboarding-v2-zh/...`. The `OnboardingApi` import from `@/lib/onboarding/api` is unchanged (the seam is shared).
- **Edit 4.4 (function signature):** Function name `OnboardingV2WizardZh` instead of `OnboardingV2Wizard`. Same prop shape.
- **Edit 4.8 (langSwitchHref):** Swap the destinations — the zh wizard's other side is en:
  ```tsx
  const langSwitchHref = (mode === "demo"
    ? "/demo/onboarding"
    : "/onboarding/v2") as Route;
  ```
- **Edit 4.9 (step 7 inline pill):** Same insertion — the zh step-7 topbar has the same Cortex `C` logo div with the same shape.
- Edits 4.2 (docstring), 4.3 (WizardMode type), 4.5 (`api = getOnboardingApi()` removal), 4.6 (storage gating), 4.7 (handleEnterDiscover branching): identical to Task 3.

The zh page's docstring is in Traditional Chinese — you can either translate the new docstring to zh or keep it in English with a one-line zh note at the top. Either is fine; the existing zh primitives.tsx mixes English and zh in its file header so there's no firm convention. Recommend: keep the new docstring in English, since it describes a build-time/architectural concept ("live vs demo mode") that's more grep-friendly in English.

- [ ] **Step 4: Slim the live zh page**

Replace `web/src/app/(auth)/onboarding/v2/zh-TW/page.tsx` with:

```tsx
"use client";

import { useMemo } from "react";

import { completeV2Onboarding } from "@/app/(auth)/onboarding/v2/complete-actions";
import { OnboardingV2WizardZh } from "@/components/onboarding-v2-zh/wizard";
import { getOnboardingApi } from "@/lib/onboarding/api";

export default function OnboardingV2ZhPage() {
  const api = useMemo(() => getOnboardingApi(), []);
  return (
    <OnboardingV2WizardZh
      mode="live"
      api={api}
      onComplete={completeV2Onboarding}
    />
  );
}
```

- [ ] **Step 5: Run the zh live regression tests**

From `web/`: `npm test -- src/components/onboarding-v2-zh/__tests__/wizard.live.test.tsx`
Expected: all 5 tests PASS.

- [ ] **Step 6: Run typecheck**

From `web/`: `npm run type-check`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add web/src/components/onboarding-v2-zh/wizard.tsx web/src/components/onboarding-v2-zh/__tests__/wizard.live.test.tsx "web/src/app/(auth)/onboarding/v2/zh-TW/page.tsx"
git commit -m "refactor(onboarding-v2-zh): extract wizard into shared client component"
```

If `index.lock` collides with parallel Task 3, retry after one second.

---

## Task 5: Demo behaviour tests for en wizard

> **Parallelizable with Tasks 6, 7, 8** — disjoint file set from all three. Depends on Task 3 being complete.

**Files:**
- Create: `web/src/components/onboarding-v2/__tests__/wizard.demo.test.tsx`

The wizard.tsx already supports `mode="demo"` from Task 3 (the storage gates and `handleEnterDiscover` branch were baked in during the lift). This task is purely test additions that lock the demo behaviour.

- [ ] **Step 1: Write the demo behaviour test**

Create `web/src/components/onboarding-v2/__tests__/wizard.demo.test.tsx`:

```tsx
/**
 * Demo-mode behaviour for the shared wizard. Pairs with wizard.live.test.tsx;
 * both files reuse the same makeOkApi helper-shape but test divergent
 * outcomes.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  CRAWL_TASKS,
  DEPLOY_AGENTS,
  DEPLOY_LOG,
  EXTRACTED_BRAND,
  LIVE_QUESTIONS,
  MEDIA_NETWORK,
  VOICE_TONES,
} from "@/components/onboarding-v2/data";
import { OnboardingV2Wizard } from "@/components/onboarding-v2/wizard";
import type { OnboardingApi } from "@/lib/onboarding/api";
import { router } from "@tests/helpers/session-mock-state";

function makeOkApi(): OnboardingApi {
  return {
    analyzeBrand: vi.fn(async () => EXTRACTED_BRAND),
    getCrawlTasks: vi.fn(async () => CRAWL_TASKS),
    getMediaNetwork: vi.fn(async () => MEDIA_NETWORK),
    getLiveQuestions: vi.fn(async () => LIVE_QUESTIONS),
    getVoiceTones: vi.fn(async () => VOICE_TONES),
    getDeployAgents: vi.fn(async () => DEPLOY_AGENTS),
    getDeployLog: vi.fn(async () => DEPLOY_LOG),
  };
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("OnboardingV2Wizard — mode='demo'", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("renders step 0 on mount even if the live completion flag is pre-set", async () => {
    window.localStorage.setItem("cortex.onboarding.v2", "complete");
    render(<OnboardingV2Wizard mode="demo" api={makeOkApi()} />);

    // No rehydrate — wizard ignores the flag.
    expect(
      await screen.findByRole("button", { name: /analyze my brand/i }),
    ).toBeInTheDocument();
  });

  it("renders the Demo badge on the rail topbar (step 0)", () => {
    render(<OnboardingV2Wizard mode="demo" api={makeOkApi()} />);
    expect(screen.getByText("Demo")).toBeInTheDocument();
  });

  it("Set up later does NOT write to localStorage in demo mode", () => {
    render(<OnboardingV2Wizard mode="demo" api={makeOkApi()} />);

    fireEvent.click(screen.getByRole("button", { name: /set up later/i }));
    expect(window.localStorage.getItem("cortex.onboarding.v2")).toBeNull();
  });

  it("Enter Discover restarts the wizard and never calls router.push", async () => {
    render(<OnboardingV2Wizard mode="demo" api={makeOkApi()} />);

    fireEvent.click(screen.getByRole("button", { name: /set up later/i }));
    const enterDiscover = await screen.findByRole("button", {
      name: /enter discover/i,
    });
    fireEvent.click(enterDiscover);

    // Restarted: back to step 0 (the Analyze button is visible again).
    expect(
      await screen.findByRole("button", { name: /analyze my brand/i }),
    ).toBeInTheDocument();
    expect(router.push).not.toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run the test**

From `web/`: `npm test -- src/components/onboarding-v2/__tests__/wizard.demo.test.tsx`
Expected: all 4 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add web/src/components/onboarding-v2/__tests__/wizard.demo.test.tsx
git commit -m "test(onboarding-v2): lock demo-mode behaviour for shared wizard"
```

If `index.lock` collides with parallel siblings, retry once.

---

## Task 6: Demo behaviour tests for zh wizard

> **Parallelizable with Tasks 5, 7, 8.** Depends on Task 4 being complete.

**Files:**
- Create: `web/src/components/onboarding-v2-zh/__tests__/wizard.demo.test.tsx`

Mirror of Task 5 in the zh tree.

- [ ] **Step 1: Write the test**

Create `web/src/components/onboarding-v2-zh/__tests__/wizard.demo.test.tsx` with the same shape as Task 5 Step 1, substituting:
- `@/components/onboarding-v2/` → `@/components/onboarding-v2-zh/`
- `OnboardingV2Wizard` → `OnboardingV2WizardZh`
- Button selectors with zh copy (mirror the substitutions from Task 4 Step 1).

The same `makeOkApi` helper and `localStorage` assertions apply unchanged — the demo behaviour matrix is identical across locales.

- [ ] **Step 2: Run the test**

From `web/`: `npm test -- src/components/onboarding-v2-zh/__tests__/wizard.demo.test.tsx`
Expected: all 4 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add web/src/components/onboarding-v2-zh/__tests__/wizard.demo.test.tsx
git commit -m "test(onboarding-v2-zh): lock demo-mode behaviour for shared wizard"
```

---

## Task 7: Create en demo route — server page + client wrapper + smoke test

> **Parallelizable with Tasks 5, 6, 8.** Depends on Task 3 being complete.

**Files:**
- Create: `web/src/app/demo/onboarding/page.tsx` (server component — metadata export only)
- Create: `web/src/app/demo/onboarding/client.tsx` (client component — wizard wiring)
- Create: `web/src/app/demo/onboarding/__tests__/page.test.tsx` (smoke test for both)

The server/client split is necessary because Next App Router only respects `export const metadata` on **server** components, and the wizard wiring (`useMemo` to instantiate the API adapter) needs a **client** component. Two tiny files achieve both.

- [ ] **Step 1: Write the smoke test first**

Create `web/src/app/demo/onboarding/__tests__/page.test.tsx`:

```tsx
/**
 * Smoke test for the en demo route. Verifies:
 *   - the server page exports a metadata.title for the browser tab,
 *   - the client wrapper renders <OnboardingV2Wizard> with mode="demo" and
 *     a MockOnboardingApi instance (NOT the live HTTP-or-mock factory output).
 *
 * Mocks the wizard so the test exercises only the wiring, not the wizard
 * body (which has its own dedicated tests in components/onboarding-v2/__tests__).
 */
import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { MockOnboardingApi } from "@/lib/onboarding/mock-api";

const wizardSpy = vi.fn();
vi.mock("@/components/onboarding-v2/wizard", () => ({
  OnboardingV2Wizard: (props: unknown) => {
    wizardSpy(props);
    return null;
  },
}));

import { DemoOnboardingClient } from "@/app/demo/onboarding/client";
import DemoOnboardingPage, { metadata } from "@/app/demo/onboarding/page";

describe("/demo/onboarding (en)", () => {
  it("server page exports metadata with the demo tab title", () => {
    expect(metadata.title).toBe("Cortex · Demo");
  });

  it("server page renders the client wrapper", () => {
    const { container } = render(<DemoOnboardingPage />);
    expect(container).toBeTruthy();
  });

  it("client wrapper renders OnboardingV2Wizard with mode='demo' and a MockOnboardingApi instance", () => {
    wizardSpy.mockClear();
    render(<DemoOnboardingClient />);

    expect(wizardSpy).toHaveBeenCalledTimes(1);
    const props = wizardSpy.mock.calls[0][0] as {
      mode: string;
      api: unknown;
      onComplete?: unknown;
    };
    expect(props.mode).toBe("demo");
    expect(props.api).toBeInstanceOf(MockOnboardingApi);
    expect(props.onComplete).toBeUndefined();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

From `web/`: `npm test -- src/app/demo/onboarding/__tests__/page.test.tsx`
Expected: FAIL with `Failed to resolve import "@/app/demo/onboarding/client"`.

- [ ] **Step 3: Create the client wrapper**

Create `web/src/app/demo/onboarding/client.tsx`:

```tsx
"use client";

import { useMemo } from "react";

import { OnboardingV2Wizard } from "@/components/onboarding-v2/wizard";
import { MockOnboardingApi } from "@/lib/onboarding/mock-api";

export function DemoOnboardingClient() {
  // Force the mock adapter regardless of the build-time NEXT_PUBLIC_CORTEX_ONBOARDING_HTTP
  // flag. The demo flow is auth-free; it must never hit real cortex-api.
  const api = useMemo(() => new MockOnboardingApi(), []);
  return <OnboardingV2Wizard mode="demo" api={api} />;
}
```

- [ ] **Step 4: Create the server page**

Create `web/src/app/demo/onboarding/page.tsx`:

```tsx
import type { Metadata } from "next";

import { DemoOnboardingClient } from "./client";

export const metadata: Metadata = {
  title: "Cortex · Demo",
};

export default function DemoOnboardingPage() {
  return <DemoOnboardingClient />;
}
```

- [ ] **Step 5: Run the smoke test**

From `web/`: `npm test -- src/app/demo/onboarding/__tests__/page.test.tsx`
Expected: all 3 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add web/src/app/demo/onboarding/page.tsx web/src/app/demo/onboarding/client.tsx web/src/app/demo/onboarding/__tests__/page.test.tsx
git commit -m "feat(demo): /demo/onboarding (en) renders wizard in demo mode"
```

---

## Task 8: Create zh demo route — server page + client wrapper + smoke test

> **Parallelizable with Tasks 5, 6, 7.** Depends on Task 4 being complete.

**Files:**
- Create: `web/src/app/demo/onboarding/zh-TW/page.tsx`
- Create: `web/src/app/demo/onboarding/zh-TW/client.tsx`
- Create: `web/src/app/demo/onboarding/zh-TW/__tests__/page.test.tsx`

Mirror of Task 7 in zh.

- [ ] **Step 1: Write the smoke test**

Create `web/src/app/demo/onboarding/zh-TW/__tests__/page.test.tsx` with the same shape as Task 7 Step 1, substituting:
- `@/components/onboarding-v2/wizard` → `@/components/onboarding-v2-zh/wizard`
- `OnboardingV2Wizard` → `OnboardingV2WizardZh`
- `@/app/demo/onboarding/client` → `@/app/demo/onboarding/zh-TW/client`
- `@/app/demo/onboarding/page` → `@/app/demo/onboarding/zh-TW/page`
- `DemoOnboardingClient` → `DemoOnboardingZhClient`
- `DemoOnboardingPage` → `DemoOnboardingZhPage`
- Test description: `/demo/onboarding/zh-TW (zh)` instead of `/demo/onboarding (en)`.
- `metadata.title` expected value: `"Cortex · 體驗版"` instead of `"Cortex · Demo"`.

The `MockOnboardingApi` instance check stays — the adapter is shared between languages.

- [ ] **Step 2: Run the test to verify it fails**

From `web/`: `npm test -- src/app/demo/onboarding/zh-TW/__tests__/page.test.tsx`
Expected: FAIL with `Failed to resolve import "@/app/demo/onboarding/zh-TW/client"`.

- [ ] **Step 3: Create the zh client wrapper**

Create `web/src/app/demo/onboarding/zh-TW/client.tsx`:

```tsx
"use client";

import { useMemo } from "react";

import { OnboardingV2WizardZh } from "@/components/onboarding-v2-zh/wizard";
import { MockOnboardingApi } from "@/lib/onboarding/mock-api";

export function DemoOnboardingZhClient() {
  const api = useMemo(() => new MockOnboardingApi(), []);
  return <OnboardingV2WizardZh mode="demo" api={api} />;
}
```

- [ ] **Step 4: Create the zh server page**

Create `web/src/app/demo/onboarding/zh-TW/page.tsx`:

```tsx
import type { Metadata } from "next";

import { DemoOnboardingZhClient } from "./client";

export const metadata: Metadata = {
  title: "Cortex · 體驗版",
};

export default function DemoOnboardingZhPage() {
  return <DemoOnboardingZhClient />;
}
```

- [ ] **Step 5: Run the smoke test**

From `web/`: `npm test -- src/app/demo/onboarding/zh-TW/__tests__/page.test.tsx`
Expected: all 3 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add web/src/app/demo/onboarding/zh-TW/page.tsx web/src/app/demo/onboarding/zh-TW/client.tsx web/src/app/demo/onboarding/zh-TW/__tests__/page.test.tsx
git commit -m "feat(demo): /demo/onboarding/zh-TW renders wizard in demo mode"
```

---

## Task 9: Full lint + test + typecheck pass

**Files:** No code changes expected — this is the catch-all sweep.

- [ ] **Step 1: Run the full web test suite**

Run from `web/`: `npm test`
Expected: every test PASSES (including the eight wizard tests added across Tasks 3–8).

- [ ] **Step 2: Run lint**

Run from `web/`: `npm run lint`
Expected: PASS with no warnings. If a `react-hooks/exhaustive-deps` warning fires on the wizard mount effect, leave the `eslint-disable-next-line` comment in place (it's intentional — see Task 3 Step 3).

- [ ] **Step 3: Run typecheck**

Run from `web/`: `npm run type-check`
Expected: PASS.

- [ ] **Step 4: Run the production build**

Run from `web/`: `npm run build`
Expected: PASS. The new routes `/demo/onboarding` and `/demo/onboarding/zh-TW` appear in the route summary at the end of the build output. Next App Router's typedRoutes accepts the new paths because they exist on disk.

- [ ] **Step 5: Commit any fixes from this sweep**

If the sweep surfaced fixes (lint, type, or test), commit them with a focused message; otherwise skip:

```bash
git add -A
git commit -m "chore(onboarding-v2): post-extraction lint/type/test fixes"
```

If there are no fixes, move on without committing.

---

## Task 10: Manual smoke walkthrough

**Files:** None. This is a wet-finger check of the actual flow in a browser before opening the PR.

- [ ] **Step 1: Start the dev server**

Run from `web/`: `npm run dev`
Wait for the line `Ready in ...` and the local URL.

- [ ] **Step 2: Walk the en demo flow in an incognito window**

Open `http://localhost:3000/demo/onboarding` in an incognito window (no session). Verify:

- The page loads without redirecting to `/signin`.
- The teal topbar shows the Cortex `C` block, a small "Demo" pill to its right, the step rail, the language switch, and "Set up later".
- The browser tab title reads `Cortex · Demo`.
- Step 0 shows the URL field pre-filled with `acmebank.asia`.
- Click "Analyze with AI" → crawl animation runs → review screen appears.
- Click through to step 5 (Launch) → click "Launch" → the launch overlay plays → arrive at "Brand Agent online".
- The step 7 light topbar also shows the "Demo" pill (this one renders dark text on light background, while the step 0-5 pill renders light text on dark background — both are correct).
- Click "Enter Discover" → the wizard returns to step 0; the browser does NOT navigate to `/brand/dashboard`.
- Reload the page → step 0 again (storage is a no-op).
- Click the language switch → URL changes to `/demo/onboarding/zh-TW`.

- [ ] **Step 3: Walk the zh demo flow**

The zh demo is now active in the same tab from Step 2. Verify the same checklist with zh-TW copy:

- Tab title `Cortex · 體驗版`.
- Step rail in zh; "稍後再設定" button instead of "Set up later".
- Demo pill present on both topbars (steps 0–5 and step 7).
- Step 7 says `Brand Agent 已上線`.
- Click "進入 Discover" → returns to step 0; no navigation.
- Language switch goes back to `/demo/onboarding`.

- [ ] **Step 4: Verify live onboarding is unaffected**

In a separate incognito window (with a valid signed-in session if one exists locally, or any test brand), visit `/onboarding/v2`. Verify the existing live behaviour is unchanged:

- No "Demo" pill anywhere.
- Set up later writes `cortex.onboarding.v2 = "complete"` to localStorage (check via DevTools).
- After completion, "Enter Discover" navigates to `/brand/dashboard`.

- [ ] **Step 5: Stop the dev server and prepare the PR**

`Ctrl-C` the dev server. The branch is ready for review.

```bash
git log --oneline -10
```

You should see commits from Tasks 1, 2, 3, 4, 5, 6, 7, 8, and (optionally) 9 — a clean linear history corresponding to the task numbers.

---

## Done. PR-ready when:

- All eight wizard tests + two page tests pass.
- `npm run lint`, `npm run type-check`, and `npm run build` are green.
- Manual walkthrough (Task 10) ticks all five sub-steps.
- The live `/onboarding/v2` flow is byte-for-byte the same user-facing behaviour as before the lift (regression net in Tasks 3, 4 confirms this in CI).
