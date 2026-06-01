"use server";

// Dev-bypass: return fixture data so the report hero renders without cortex-api.
const DEV_BYPASS_AUTH = process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === "true";

/**
 * Server actions for brand_report UI-state + report fetching.
 *
 * These are called from the client-side `DiscoverDashboard` and related
 * components. All cortex-api calls are server-side (token never leaves server).
 *
 * Design:
 *   - loadReportState  — read ui-state + latest report in one roundtrip pair
 *   - consumeCelebrate — idempotent; called when celebration modal is dismissed
 *   - dismissHero      — called when hero card × is clicked
 *   - retryReport      — re-trigger generation from the hero failed-state CTA,
 *                        then return the freshly re-loaded state
 *
 * NOTE: celebration arming happens in the onboarding flow (`completeV2Onboarding`
 * calls `armReportCelebrate`); the dashboard only READS + CONSUMES + RETRIES.
 */

import { auth } from "@/lib/auth";
import {
  consumeReportCelebrate,
  dismissReportHero,
  generateReport,
  getReportUiState,
  listBrandReports,
  fetchBrandReport,
  type ReportUiStateResponse,
  type ReportVersionItem,
  type ReportEnvelope,
} from "@/lib/cortex-api";
import type { ReportState } from "./report-types";

// ---------------------------------------------------------------------------
// Auth helper — shared by all server actions in this file.
// ---------------------------------------------------------------------------

async function _claims() {
  const session = await auth();
  const activeContext = session?.user?.activeContext;
  // Gate on the brand context only — NOT on cortexUserId. The brand-scoped
  // cortex-api calls (ui-state / reports / report) authorize on the brand
  // context in the signed token; cortexUserId is not required (the Knowledge
  // Base server component proves this — it calls listBrandReports with
  // `cortexUserId ?? ""` and succeeds). Bailing on a missing cortexUserId here
  // silently returned defaults (celebratePending=false), so the hero +
  // celebration never showed even when the report was ready. Match the KB's
  // tolerance: fall back to "" instead of returning null.
  if (!activeContext || activeContext.kind !== "brand" || !activeContext.id)
    return null;
  return {
    cortexUserId: session?.user?.cortexUserId ?? "",
    email: session?.user?.email ?? "",
    displayName: session?.user?.name ?? null,
    activeContext,
  };
}

// ---------------------------------------------------------------------------
// Combined loader — ui-state + latest report (if any)
// ---------------------------------------------------------------------------

/**
 * Load the report hero's full state in one server round-trip pair.
 *
 * Returns defaults (no celebration, no hero dismissal, no report) if the
 * session is invalid — the component degrades gracefully.
 */
export async function loadReportState(): Promise<ReportState> {
  if (DEV_BYPASS_AUTH) {
    const { READY_FIXTURE } = await import(
      "@/components/brand-dashboard/report-surface-fixture"
    );
    return {
      uiState: { celebratePending: false, heroDismissed: false, celebrateReady: false },
      latestReport: READY_FIXTURE,
      brandId: "00000000-0000-0000-0000-000000000000",
    };
  }

  const claims = await _claims();
  if (!claims) {
    return {
      uiState: { celebratePending: false, heroDismissed: false, celebrateReady: false },
      latestReport: null,
      brandId: null,
    };
  }
  const brandId = claims.activeContext.id;

  // Both requests fire; if either fails, degrade gracefully.
  const [uiState, versions] = await Promise.all([
    getReportUiState(claims, brandId).catch(() => ({
      celebratePending: false,
      heroDismissed: false,
      celebrateReady: false,
    })),
    listBrandReports(claims, brandId).catch(() => [] as ReportVersionItem[]),
  ]);

  // Fetch the latest report envelope (first in list = newest, by server ordering).
  const latest = versions[0] ?? null;
  let latestReport: ReportEnvelope | null = null;
  if (latest) {
    latestReport = await fetchBrandReport(claims, brandId, latest.reportId).catch(
      () => null,
    );
  }

  return { uiState, latestReport, brandId };
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

export async function consumeCelebrate(): Promise<void> {
  const claims = await _claims();
  if (!claims) return;
  try {
    await consumeReportCelebrate(claims, claims.activeContext.id);
  } catch {
    // Resilient — failure is non-fatal; worst case is the modal shows again
    // on next load (still idempotent once the server processes it).
  }
}

export async function dismissHero(): Promise<void> {
  const claims = await _claims();
  if (!claims) return;
  try {
    await dismissReportHero(claims, claims.activeContext.id);
  } catch {
    // Resilient — failure means the hero shows again, which is acceptable.
  }
}

/**
 * Re-trigger report generation (hero failed-state "重試" CTA), then return the
 * freshly re-loaded report state so the caller can re-render (generating →
 * eventually ready/failed via polling). Resilient: a failed re-trigger still
 * returns the current state rather than throwing.
 */
export async function retryReport(): Promise<ReportState> {
  const claims = await _claims();
  if (claims) {
    try {
      await generateReport(claims, claims.activeContext.id);
    } catch {
      // Non-fatal — fall through and return whatever state we can load.
    }
  }
  return loadReportState();
}
