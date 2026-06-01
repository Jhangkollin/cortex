/**
 * Structural call-site guard for SP-QUESTIONS (mirrors orchestrator-media-callsite.test.ts).
 *
 * THE INVARIANT (for BOTH the EN and 繁中 orchestrators):
 *   1. `loadModeled` (runs at mount) must NOT reference `getLiveQuestions`.
 *   2. `runAnalyze` MUST reference `getLiveQuestions`.
 *   3. Inside `runAnalyze`, the `getLiveQuestions` call must come AFTER the
 *      `analyzeBrand` call (i.e. questions are fetched post-analyze, when a
 *      brand profile + active brand context exist).
 *
 * This mirrors the d8345ff pattern from SP-MEDIA: weekly questions require
 * an active brand session (set up by analyze), so they must NOT be loaded at
 * mount time in `loadModeled`.
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
  "onboarding-v2 orchestrator (%s) — getLiveQuestions call-site invariant",
  (_locale, file) => {
    const src = readFileSync(file, "utf8");

    const loadModeled = regionBetween(src, "const loadModeled = useCallback(", [
      "const runAnalyze = useCallback(",
    ]);
    const runAnalyze = regionBetween(src, "const runAnalyze = useCallback(", [
      "\n  useEffect(",
      "const restart = useCallback(",
    ]);

    it("loadModeled (mount-time) does NOT call getLiveQuestions", () => {
      expect(loadModeled).not.toContain("getLiveQuestions");
    });

    it("runAnalyze calls getLiveQuestions", () => {
      expect(runAnalyze).toContain("getLiveQuestions");
    });

    it("getLiveQuestions is called AFTER analyzeBrand (post-analyze)", () => {
      const analyzeAt = runAnalyze.indexOf("analyzeBrand");
      const questionsAt = runAnalyze.indexOf("getLiveQuestions");
      expect(analyzeAt, "analyzeBrand not found in runAnalyze").toBeGreaterThanOrEqual(0);
      expect(questionsAt, "getLiveQuestions not found in runAnalyze").toBeGreaterThanOrEqual(0);
      expect(questionsAt).toBeGreaterThan(analyzeAt);
    });
  },
);
