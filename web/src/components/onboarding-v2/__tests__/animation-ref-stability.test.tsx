/**
 * Regression suite for PR #29 Code Review "Issue 3": the per-step animation
 * effects must NOT couple to array-reference identity.
 *
 * Today `MockOnboardingApi` returns the same module-level constant on every
 * call, so `deployAgents` / `deployLog` / `crawlTasks` are reference-stable
 * and these effects behave correctly. The next adapter (`HttpOnboardingApi`,
 * SP-3a) will allocate a FRESH array per fetch with identical contents.
 *
 * Concrete failure mode: each animation effect lists the array in its
 * dependency list and schedules the step `setTimeout` *inside* that effect.
 * React compares deps by reference, so a parent re-render handing back a
 * fresh-but-equal array tears down the in-flight timer (cleanup) and starts
 * a new one. If such re-renders arrive faster than one animation step's
 * delay — entirely plausible when an unrelated wizard state change coincides
 * with a refetch — the pending tick is cancelled before it ever fires and
 * the animation stalls forever.
 *
 * Strategy: advance fake timers in slices SMALLER than a single step delay,
 * re-rendering with a brand-new (deep-cloned, `Object.is === false`) array
 * between every slice. Total elapsed time crosses several step thresholds.
 * A correctly-decoupled effect still advances the counter; a ref-coupled
 * effect never does because the timer is perpetually cancelled.
 *
 * Assertions target the OBSERVABLE counter each component renders.
 */
import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  CRAWL_TASKS,
  DEPLOY_AGENTS,
  DEPLOY_LOG,
  MEDIA_NETWORK,
} from "@/components/onboarding-v2/data";
import { LaunchOverlay } from "@/components/onboarding-v2/launch-overlay";
import { StepCrawl } from "@/components/onboarding-v2/step-crawl";

const clone = <T,>(a: T[]): T[] => a.map((x) => ({ ...x }));

beforeEach(() => {
  vi.useFakeTimers();
  // jsdom does not implement Element.prototype.scrollTo; the deploy-log
  // auto-scroll effect calls it. Stub it so the component can mount.
  Element.prototype.scrollTo = vi.fn();
});

afterEach(() => {
  vi.runOnlyPendingTimers();
  vi.useRealTimers();
});

describe("StepCrawl — animation is decoupled from crawlTasks array identity", () => {
  it("keeps advancing while a fresh-but-equal array arrives faster than a step", () => {
    let tasks = clone(CRAWL_TASKS);
    const { rerender } = render(
      <StepCrawl
        url="acmebank.asia"
        ready={false}
        brand={null}
        onComplete={() => {}}
        crawlTasks={tasks}
      />,
    );
    expect(screen.getByText(`0 / ${CRAWL_TASKS.length}`)).toBeInTheDocument();

    // First step delay is 600 * PACE(1.5) = 900ms. Tick in 150ms slices,
    // re-rendering with a fresh array every slice. ~3000ms total elapses —
    // enough to cross the first two step thresholds.
    for (let slice = 0; slice < 20; slice++) {
      act(() => {
        vi.advanceTimersByTime(150);
      });
      const next = clone(CRAWL_TASKS);
      expect(Object.is(tasks, next)).toBe(false);
      tasks = next;
      act(() => {
        rerender(
          <StepCrawl
            url="acmebank.asia"
            ready={false}
            brand={null}
            onComplete={() => {}}
            crawlTasks={tasks}
          />,
        );
      });
    }

    expect(
      screen.queryByText(`0 / ${CRAWL_TASKS.length}`),
    ).not.toBeInTheDocument();
  });
});

describe("LaunchOverlay — animation is decoupled from deploy array identity", () => {
  it("keeps advancing while fresh-but-equal arrays arrive faster than a step", () => {
    let agents = clone(DEPLOY_AGENTS);
    let log = clone(DEPLOY_LOG);
    let media = clone(MEDIA_NETWORK);
    const { rerender } = render(
      <LaunchOverlay
        onDone={() => {}}
        deployAgents={agents}
        deployLog={log}
        mediaNetwork={media}
      />,
    );
    expect(screen.getByText(`0 / ${DEPLOY_AGENTS.length}`)).toBeInTheDocument();

    // AGENT_STEP_MS = 280 * PACE(3) = 840ms. Tick in 140ms slices,
    // re-rendering with brand-new arrays every slice; ~2800ms total.
    for (let slice = 0; slice < 20; slice++) {
      act(() => {
        vi.advanceTimersByTime(140);
      });
      const a = clone(DEPLOY_AGENTS);
      expect(Object.is(agents, a)).toBe(false);
      agents = a;
      log = clone(DEPLOY_LOG);
      media = clone(MEDIA_NETWORK);
      act(() => {
        rerender(
          <LaunchOverlay
            onDone={() => {}}
            deployAgents={agents}
            deployLog={log}
            mediaNetwork={media}
          />,
        );
      });
    }

    expect(
      screen.queryByText(`0 / ${DEPLOY_AGENTS.length}`),
    ).not.toBeInTheDocument();
  });
});
