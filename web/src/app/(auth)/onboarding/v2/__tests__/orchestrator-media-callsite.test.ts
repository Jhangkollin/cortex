/**
 * Regression guard for the SP-MEDIA orchestrator bug (commit d8345ff).
 *
 * THE BUG: `getMediaNetwork()` became a REAL cortex-api call (server action →
 * cortex-api). It was left inside the wizard's mount-time `loadModeled()`
 * `Promise.all` of instant modeled data. At mount there is no brand session /
 * profile, so the server action threw in `claimsFromSession` BEFORE any fetch,
 * and `Promise.all`'s all-or-nothing also wiped the other modeled datasets —
 * step 3 (and the rest) rendered empty, zero requests reached the API.
 *
 * THE INVARIANT this locks (for BOTH the EN and 繁中 orchestrators):
 *   1. `loadModeled` (runs at mount) must NOT reference `getMediaNetwork`.
 *   2. `runAnalyze` MUST reference `getMediaNetwork`.
 *   3. Inside `runAnalyze`, the `getMediaNetwork` call must come AFTER the
 *      `analyzeBrand` call (i.e. media is fetched post-analyze, when a brand
 *      profile + active brand context exist).
 *
 * This is a source-level (lint-like) guard on purpose: the failure mode was
 * structural — *which lifecycle function calls the seam* — not logic inside a
 * function. It also intentionally reads the source as text instead of
 * importing `page.tsx`, which is unimportable under vitest/jsdom because the
 * NextAuth module graph pulls `next/server` (the same wall that reds
 * `page-load-states.test.tsx`). A full-stack Playwright e2e is tracked as a
 * separate follow-up; it needs a stubbed cortex-api (real Claude/Databricks
 * cannot run in CI).
 *
 * If a future refactor renames `loadModeled`/`runAnalyze` or restructures the
 * data flow, update this guard deliberately — do not delete the invariant.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

import { describe, expect, it } from "vitest";

const here = path.dirname(fileURLToPath(import.meta.url));
// Orchestrator (loadModeled/runAnalyze) was lifted out of page.tsx into the
// shared OnboardingV2Wizard component when the public /demo/onboarding route
// landed. The structural invariants this guard locks now live in wizard.tsx.
const PAGES = {
  EN: path.resolve(here, "../../../../../components/onboarding-v2/wizard.tsx"),
  "zh-TW": path.resolve(here, "../../../../../components/onboarding-v2-zh/wizard.tsx"),
};

/** Slice the source between two anchor substrings (start inclusive, end exclusive). */
function regionBetween(src: string, startAnchor: string, endAnchors: string[]): string {
  const start = src.indexOf(startAnchor);
  expect(
    start,
    `anchor not found: "${startAnchor}" — orchestrator restructured? update this guard deliberately`,
  ).toBeGreaterThanOrEqual(0);
  let end = src.length;
  for (const a of endAnchors) {
    const i = src.indexOf(a, start + startAnchor.length);
    if (i >= 0) end = Math.min(end, i);
  }
  expect(
    end,
    `no end anchor (${endAnchors.join(" | ")}) after "${startAnchor}"`,
  ).toBeLessThan(src.length + 1);
  return src.slice(start, end);
}

describe.each(Object.entries(PAGES))(
  "onboarding-v2 orchestrator (%s) — getMediaNetwork call-site invariant",
  (_locale, file) => {
    const src = readFileSync(file, "utf8");

    const loadModeled = regionBetween(src, "const loadModeled = useCallback(", [
      "const runAnalyze = useCallback(",
    ]);
    const runAnalyze = regionBetween(src, "const runAnalyze = useCallback(", [
      "\n  useEffect(",
      "const restart = useCallback(",
    ]);

    it("loadModeled (mount-time) does NOT call getMediaNetwork", () => {
      expect(loadModeled).not.toContain("getMediaNetwork");
    });

    it("runAnalyze calls getMediaNetwork", () => {
      expect(runAnalyze).toContain("getMediaNetwork");
    });

    it("getMediaNetwork is called AFTER analyzeBrand (post-analyze)", () => {
      const analyzeAt = runAnalyze.indexOf("analyzeBrand");
      const mediaAt = runAnalyze.indexOf("getMediaNetwork");
      expect(analyzeAt, "analyzeBrand not found in runAnalyze").toBeGreaterThanOrEqual(0);
      expect(mediaAt, "getMediaNetwork not found in runAnalyze").toBeGreaterThanOrEqual(0);
      expect(mediaAt).toBeGreaterThan(analyzeAt);
    });
  },
);
