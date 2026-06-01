"use client";

/**
 * Brand IQ report surface — the post-onboarding hero + one-time celebration.
 *
 * Rendered at the dashboard PAGE level, ABOVE the empty/populated split, so it
 * also appears for freshly-onboarded brands. Those have 0 connected sources and
 * render <EmptyDiscover/> — which is exactly the first-report case. Previously
 * this logic lived inside <DiscoverDashboard/> and so never showed for an empty
 * brand (the most common moment a first report exists). Keeping it separate from
 * the discover stage means both states get the report hero + celebration.
 *
 * Server-side UI state (celebratePending, heroDismissed) + the latest report are
 * loaded on mount via the `loadReportState` server action. When the user just
 * onboarded the report is usually still generating, so we POLL until it's
 * ready/failed (and re-fetch on tab focus). All brand-specific content in the
 * hero/celebration comes from the REAL report — no fixtures.
 *
 * Renders nothing (null) until there is something to show, so it adds no markup
 * for brands with no report.
 */

import { useCallback, useEffect, useState, type ReactElement } from "react";

import {
  loadReportState,
  consumeCelebrate,
  dismissHero,
  retryReport,
} from "@/app/brand/dashboard/report-actions";
import type {
  ReportEnvelope,
  ReportState,
  ReportUiStateResponse,
} from "@/app/brand/dashboard/report-types";

import { BrandReportSurfaceView } from "./brand-report-surface-view";

interface ReportSurfaceState {
  loaded: boolean;
  uiState: ReportUiStateResponse;
  latestReport: ReportEnvelope | null;
  /** Local override: true once the user dismisses the hero in this session. */
  heroDismissedLocal: boolean;
  /** Local override: true once the user closes the celebration modal. */
  celebrateClosedLocal: boolean;
}

/** A report status that won't change without a new generation. */
function isTerminal(report: ReportEnvelope | null): boolean {
  return report !== null && (report.status === "ready" || report.status === "failed");
}

const POLL_INTERVAL_MS = 4_000;
const POLL_MAX_ATTEMPTS = 30; // ~2 minutes total

export interface BrandReportSurfaceProps {
  /**
   * Preview mode: seed state from the local fixture so the celebration shows,
   * and skip the mount-load + poll effects entirely. Lets the Brand IQ
   * celebration be exercised without cortex-api. The fixture is loaded
   * DYNAMICALLY (import()) only in this mode, so its ~178 lines never ship in
   * the production dashboard bundle. Defaults to false.
   */
  preview?: boolean;
}

/** The initial "nothing to show yet" state, shared by real + preview modes. */
const EMPTY_STATE: ReportSurfaceState = {
  loaded: false,
  uiState: { celebratePending: false, heroDismissed: false, celebrateReady: false },
  latestReport: null,
  heroDismissedLocal: false,
  celebrateClosedLocal: false,
};

export function BrandReportSurface({
  preview = false,
}: BrandReportSurfaceProps = {}): ReactElement | null {
  // Both modes start "not yet loaded" so the surface renders nothing initially.
  // Preview seeds asynchronously via a dynamic import() in the effect below
  // (keeping the fixture out of the prod bundle); the real path seeds from the
  // server action. Either way the first paint is empty.
  const [state, setState] = useState<ReportSurfaceState>(EMPTY_STATE);

  // Apply a freshly-loaded ReportState into component state. Visibility of the
  // celebration is derived from the server's authoritative `celebrateReady`
  // flag (see `showCelebration`); `applyState` only records the loaded server
  // state. The local `celebrateClosedLocal` latch is set on close and never
  // cleared here, so a celebration the user closed this session never re-shows
  // even if a later poll still reports `celebrateReady` before the consume
  // round-trips.
  const applyState = useCallback((rs: ReportState) => {
    setState((prev) => ({
      ...prev,
      loaded: true,
      uiState: rs.uiState,
      latestReport: rs.latestReport,
    }));
  }, []);

  // Preview seed (preview mode only). The fixture is loaded with a dynamic
  // import() so it's split into its own chunk and never shipped in the normal
  // dashboard bundle — only fetched when ?celebrate=preview drives this mode.
  // `cancelled` guards against a stale resolution writing after unmount.
  useEffect(() => {
    if (!preview) return;
    let cancelled = false;
    void import("./report-surface-fixture").then(
      ({ READY_FIXTURE, PREVIEW_UI_STATE }) => {
        if (cancelled) return;
        setState((prev) => ({
          ...prev,
          loaded: true,
          uiState: PREVIEW_UI_STATE,
          latestReport: READY_FIXTURE,
        }));
      },
    );
    return () => {
      cancelled = true;
    };
  }, [preview]);

  // Initial load on mount.
  //
  // `ignore` guards against a stale resolution overwriting newer state under
  // StrictMode's double-invoke (or rapid remount): the cleanup flips `ignore`
  // so the resolved/rejected callbacks from a torn-down effect become no-ops.
  useEffect(() => {
    if (preview) return;
    let ignore = false;
    loadReportState()
      .then((rs) => {
        if (ignore) return;
        applyState(rs);
      })
      .catch(() => {
        if (ignore) return;
        setState((prev) => ({ ...prev, loaded: true }));
      });
    return () => {
      ignore = true;
    };
  }, [applyState, preview]);

  // Poll while a celebration is pending but the report isn't terminal yet.
  //
  // On the intended post-onboarding visit the report is usually still
  // generating, so without polling the celebration (which requires `ready`)
  // would never fire. We poll loadReportState on an interval until the report
  // is ready/failed or we hit the attempt cap, and also re-fetch when the tab
  // regains focus/visibility. The `ignore` flag + interval clear in teardown
  // prevent stale writes and leaked timers.
  const shouldPoll =
    state.loaded &&
    state.uiState.celebratePending &&
    !state.uiState.celebrateReady &&
    !state.uiState.heroDismissed &&
    !state.heroDismissedLocal &&
    !isTerminal(state.latestReport);

  useEffect(() => {
    if (preview) return;
    // The effect re-subscribes whenever `shouldPoll` changes, so inside this
    // body `shouldPoll` is always true (we early-return otherwise) — no ref
    // needed to read the latest value from the focus handler.
    if (!shouldPoll) return;

    let ignore = false;
    let attempts = 0;

    const tick = async () => {
      attempts += 1;
      try {
        const rs = await loadReportState();
        if (ignore) return;
        applyState(rs);
        if (isTerminal(rs.latestReport) || attempts >= POLL_MAX_ATTEMPTS) {
          clearInterval(interval);
        }
      } catch {
        // Transient failure — keep polling until the attempt cap.
        if (attempts >= POLL_MAX_ATTEMPTS) clearInterval(interval);
      }
    };

    const interval = setInterval(tick, POLL_INTERVAL_MS);

    // Re-fetch immediately when the tab regains focus/visibility (a user who
    // tabbed away during generation should see the result on return).
    const onVisible = () => {
      if (document.visibilityState === "visible") {
        void tick();
      }
    };
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("focus", onVisible);

    return () => {
      ignore = true;
      clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("focus", onVisible);
    };
  }, [shouldPoll, applyState, preview]);

  // Hero dismiss: local + server.
  const handleDismissHero = useCallback(() => {
    setState((prev) => ({ ...prev, heroDismissedLocal: true }));
    void dismissHero();
  }, []);

  // Celebration close: local + server consume.
  const handleCloseCelebration = useCallback(() => {
    setState((prev) => ({ ...prev, celebrateClosedLocal: true }));
    void consumeCelebrate();
  }, []);

  // Hero failed-state retry: re-trigger generation, then apply the re-loaded
  // state (back to generating → polling resumes via shouldPoll).
  const handleRetry = useCallback(() => {
    setState((prev) => ({
      ...prev,
      // Optimistically clear the failed report so the hero shows the skeleton
      // immediately; the re-loaded state replaces it.
      latestReport: prev.latestReport
        ? { ...prev.latestReport, status: "pending", error: null }
        : prev.latestReport,
    }));
    void retryReport().then((rs) => applyState(rs));
  }, [applyState]);

  const showHero =
    state.loaded &&
    !state.uiState.heroDismissed &&
    !state.heroDismissedLocal &&
    state.latestReport !== null;

  // The server's `celebrateReady` flag already encodes "a READY report exists
  // AND celebrate is pending AND not consumed", so we no longer re-check the
  // report status client-side. We still require `latestReport !== null` because
  // the modal renders the report's content, and we suppress it once the user
  // has closed it this session (`celebrateClosedLocal`).
  const showCelebration =
    state.loaded &&
    !state.celebrateClosedLocal &&
    state.uiState.celebrateReady &&
    state.latestReport !== null;

  return (
    <BrandReportSurfaceView
      showHero={showHero}
      showCelebration={showCelebration}
      report={state.latestReport}
      heroDismissed={state.uiState.heroDismissed || state.heroDismissedLocal}
      onDismissHero={handleDismissHero}
      onRetry={handleRetry}
      onCloseCelebration={handleCloseCelebration}
    />
  );
}
