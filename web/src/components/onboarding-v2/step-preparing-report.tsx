"use client";

/**
 * StepPreparingReport — the post-onboarding interstitial.
 *
 * The natural moment to celebrate the first Brand IQ report is right after the
 * user finishes onboarding ("Enter Discover"), while they're still captive —
 * NOT as a background modal on a dashboard they may already have left. This
 * component bridges that gap: it shows a "preparing your first report…" progress
 * state and polls report ui-state until the server's single `celebrateReady`
 * flag flips true with a real report attached, at which point it hands off to
 * the existing <BrandReportCelebration/> overlay.
 *
 * Wiring this into the onboarding wizard is a separate task — this component
 * only owns the preparing → celebrate → done lifecycle.
 *
 * Lifecycle:
 *   - On mount: call loadState() immediately, then poll every `pollMs`.
 *   - Not ready yet → progress state + a "Skip to dashboard" escape hatch.
 *   - Ready (celebrateReady && latestReport) → stop polling, show celebration.
 *     On celebration close → AWAIT consumeCelebrate() then onDone() (consume is
 *     awaited so the dashboard's own load runs after the flag is cleared; onDone
 *     still fires via `finally` if consume fails, and is idempotent).
 *   - `timeoutMs` elapses without ready → onDone() (the dashboard surface still
 *     shows the celebration later, so nothing is lost).
 *
 * `loadState` is injected (defaults to the real `loadReportState` server action)
 * so tests can drive the lifecycle with a fake. A `cancelled` flag guards every
 * async resolution against stale writes after unmount.
 */

import { useEffect, useRef, useState, type ReactElement } from "react";

import {
  loadReportState,
  consumeCelebrate,
} from "@/app/brand/dashboard/report-actions";
import type {
  ReportEnvelope,
  ReportState,
} from "@/app/brand/dashboard/report-types";

import { BrandReportCelebration } from "@/components/brand-dashboard/discover/brand-report-celebration";

/**
 * All user-visible copy for the interstitial. Extracted into a prop so locale
 * variants (e.g. the zh-TW sibling) can supply translated strings without
 * forking the component. English is the default (`EN_PREPARING_LABELS`).
 */
export interface PreparingReportLabels {
  /** Eyebrow above the title, e.g. "Brand Agent · working". */
  working: string;
  /** Main heading, e.g. "Preparing your first report…". */
  title: string;
  /** Supporting paragraph under the title. */
  subtitle: string;
  /** Skip / escape-hatch button label. */
  skip: string;
}

export const EN_PREPARING_LABELS: PreparingReportLabels = {
  working: "Brand Agent · working",
  title: "Preparing your first report…",
  subtitle:
    "Cortex is assembling your Brand IQ report from everything you set up during onboarding. This usually takes a moment — hang tight.",
  skip: "Skip to dashboard",
};

export interface StepPreparingReportProps {
  /** Navigate to the dashboard / finish the onboarding flow. */
  onDone: () => void;
  /** Injectable loader; defaults to the real `loadReportState` server action. */
  loadState?: () => Promise<ReportState>;
  /** Poll cadence while waiting for the report. Default 4000ms. */
  pollMs?: number;
  /** Give up and fall back to the dashboard after this long. Default 45000ms. */
  timeoutMs?: number;
  /** User-visible copy. Defaults to English (`EN_PREPARING_LABELS`). */
  labels?: PreparingReportLabels;
}

function isReady(rs: ReportState): rs is ReportState & {
  latestReport: ReportEnvelope;
} {
  return rs.uiState.celebrateReady && rs.latestReport !== null;
}

export function StepPreparingReport({
  onDone,
  loadState = loadReportState,
  pollMs = 4_000,
  timeoutMs = 45_000,
  labels = EN_PREPARING_LABELS,
}: StepPreparingReportProps): ReactElement {
  const [report, setReport] = useState<ReportEnvelope | null>(null);

  // Latch onDone / loadState in refs so the lifecycle effect doesn't re-run
  // (and restart polling) just because the parent passes fresh closures each
  // render. These are only read inside async callbacks / event handlers, never
  // during render, so syncing them in a plain effect is safe.
  const onDoneRef = useRef(onDone);
  const loadStateRef = useRef(loadState);
  useEffect(() => {
    onDoneRef.current = onDone;
    loadStateRef.current = loadState;
  });

  // Timer handles + a one-shot "done" latch live in refs so every exit path
  // (skip button, timeout fallback, celebration close) can stop polling and
  // call onDone exactly once — even paths that fire from event handlers
  // outside the lifecycle effect. Without this, clicking "Skip" left the
  // interval/timeout running, so the timeout later called onDone a SECOND time
  // (and a late ready-tick could surface the celebration a THIRD).
  const doneRef = useRef(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | undefined>(
    undefined,
  );
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(
    undefined,
  );

  const stop = () => {
    if (intervalRef.current !== undefined) clearInterval(intervalRef.current);
    if (timeoutRef.current !== undefined) clearTimeout(timeoutRef.current);
    intervalRef.current = undefined;
    timeoutRef.current = undefined;
  };

  // Single idempotent exit: halt polling and call onDone at most once.
  const finish = () => {
    if (doneRef.current) return;
    doneRef.current = true;
    stop();
    onDoneRef.current();
  };

  useEffect(() => {
    let cancelled = false;

    const tick = async () => {
      try {
        const rs = await loadStateRef.current();
        if (cancelled || doneRef.current) return;
        if (isReady(rs)) {
          stop();
          setReport(rs.latestReport);
        }
      } catch {
        // Transient failure — keep polling until the timeout fires.
      }
    };

    // Fire immediately, then on the poll cadence.
    void tick();
    intervalRef.current = setInterval(() => void tick(), pollMs);

    // Hard fallback: give up and go to the dashboard.
    timeoutRef.current = setTimeout(() => {
      if (cancelled) return;
      finish();
    }, timeoutMs);

    return () => {
      cancelled = true;
      stop();
    };
    // `stop`/`finish` only touch refs (stable); the effect intentionally keys
    // off the poll/timeout cadence alone.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pollMs, timeoutMs]);

  const handleCloseCelebration = async () => {
    // AWAIT the consume before navigating so the dashboard's own
    // loadReportState() runs AFTER the server has cleared the celebrate flag —
    // otherwise the still-true `celebrateReady` would re-show the celebration on
    // the dashboard (a re-show race). Navigation must never hang on a failed
    // consume, so finish() runs in `finally` (and finish() is idempotent).
    try {
      await consumeCelebrate();
    } finally {
      finish();
    }
  };

  if (report !== null) {
    return (
      <BrandReportCelebration
        report={report}
        // handleCloseCelebration runs onDone via `finally`, so a rejected
        // consume already navigates; swallow the rejection here so the floated
        // promise doesn't surface as an unhandled rejection.
        onClose={() => {
          handleCloseCelebration().catch(() => {});
        }}
      />
    );
  }

  return (
    <div
      style={{
        minHeight: "60vh",
        display: "grid",
        placeItems: "center",
        padding: "48px 24px",
        textAlign: "center",
      }}
    >
      <div style={{ maxWidth: 440 }}>
        <div
          aria-hidden
          style={{
            width: 64,
            height: 64,
            margin: "0 auto 24px",
            borderRadius: "50%",
            border: "3px solid var(--mly-teal-100, #B2DFDB)",
            borderTopColor: "var(--mly-teal-700, #1C726B)",
            animation: "mly-spin 0.9s linear infinite",
          }}
        />
        <div
          style={{
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            color: "var(--mly-teal-700, #1C726B)",
            marginBottom: 10,
            fontFamily: "var(--font-mono)",
          }}
        >
          {labels.working}
        </div>
        <h2
          style={{
            fontSize: 26,
            fontWeight: 700,
            color: "var(--mly-ink-900, #0E2D2C)",
            letterSpacing: "-0.015em",
            margin: "0 0 10px",
          }}
        >
          {labels.title}
        </h2>
        <p
          style={{
            color: "var(--mly-ink-600, #4B5E5C)",
            fontSize: 14,
            lineHeight: 1.6,
            margin: "0 0 24px",
          }}
        >
          {labels.subtitle}
        </p>
        <button
          type="button"
          onClick={() => finish()}
          style={{
            background: "transparent",
            color: "var(--mly-ink-500, #6B7C7A)",
            border: "1px solid var(--mly-ink-150, #D9E2E0)",
            padding: "10px 18px",
            borderRadius: 8,
            fontSize: 13,
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          {labels.skip}
        </button>
      </div>
      <style>{`
        @keyframes mly-spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
