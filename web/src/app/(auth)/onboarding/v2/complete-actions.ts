"use server";

/**
 * Server Action — final step of the v2 AI-wizard onboarding.
 *
 * Stamps the brand as onboarded via `POST /v1/brand/{brand_id}/onboarding/complete`
 * (idempotent). Must succeed before the client navigates to /brand/dashboard;
 * the /brand/* server gate redirects non-onboarded brands back to /onboarding,
 * so any unguarded navigation on failure creates a confusing redirect loop.
 *
 * Guard mirrors `manual/actions.ts` exactly — same error wording and
 * guard ordering so the two paths read consistently.
 */

import { auth } from "@/lib/auth";
import {
  armReportCelebrate,
  completeOnboarding,
  generateReport,
} from "@/lib/cortex-api";

export async function completeV2Onboarding(): Promise<void> {
  const session = await auth();
  if (!session?.user?.email) {
    throw new Error("Not signed in.");
  }
  if (!session.user.cortexUserId) {
    throw new Error(
      "Sign-in did not complete. Please sign out and sign in again.",
    );
  }
  const activeContext = session.user.activeContext;
  if (!activeContext || activeContext.kind !== "brand" || !activeContext.id) {
    throw new Error(
      "No active brand context. Pick a workspace from the persona picker first.",
    );
  }

  const claims = {
    cortexUserId: session.user.cortexUserId,
    email: session.user.email,
    displayName: session.user.name ?? null,
    activeContext,
  };

  // Onboarding stamp must succeed before the redirect (the /brand/* gate
  // bounces non-onboarded brands).
  await completeOnboarding(claims, activeContext.id);

  // Post-onboarding orchestration (both resilient — a failure must NOT block
  // entering the dashboard; the dashboard degrades to a "no report yet" state):
  //   1. Trigger async report generation so it starts cooking immediately.
  //   2. Arm the celebration flag. brand_report owns this state (its own
  //      table), so the web handoff is the one arming path. The founder holds
  //      VIEW_BRAND_DASHBOARD (verified — ADMIN gets every capability), so the
  //      capability-gated arm endpoint succeeds for first-time onboarding.
  try {
    await generateReport(claims, activeContext.id);
  } catch {
    // Non-fatal — dashboard degrades to "no report yet" state.
  }
  try {
    await armReportCelebrate(claims, activeContext.id);
  } catch {
    // Non-fatal — the celebration just won't show; everything else proceeds.
  }
}
