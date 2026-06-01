"use server";

/**
 * Server Actions — analyze pipeline bridge for the onboarding v2 wizard.
 *
 * The `"use client"` wizard cannot call `@/lib/cortex-api` (server-only:
 * imports `cortex-token` which needs `NEXTAUTH_SECRET`). These two thin
 * actions wrap Task 11's `startAnalyze` / `pollAnalyze`, deriving `brandId`
 * + signed-token claims from the authenticated NextAuth session server-side
 * so nothing scoping-related is ever trusted from the client.
 *
 * Auth contract mirrors `completeBrandOnboarding`: the caller is the founder
 * of a freshly created brand workspace, so they hold an active brand
 * `activeContext` (ADMIN → `EDIT_BRAND_SETTINGS`). Missing session /
 * cortexUserId / active brand context bails with a descriptive error rather
 * than 401-ing inside cortex-api.
 */

import { auth } from "@/lib/auth";
import { type AnalyzeJobDTO, pollAnalyze, startAnalyze } from "@/lib/cortex-api";
import type { CortexTokenClaims } from "@/lib/cortex-token";

async function claimsFromSession(): Promise<{
  claims: CortexTokenClaims;
  brandId: string;
}> {
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
    throw new Error("no active brand context");
  }

  return {
    claims: {
      cortexUserId: session.user.cortexUserId,
      email: session.user.email,
      displayName: session.user.name ?? null,
      activeContext,
    },
    brandId: activeContext.id,
  };
}

export async function startAnalyzeAction(url: string): Promise<AnalyzeJobDTO> {
  const { claims, brandId } = await claimsFromSession();
  return startAnalyze(claims, brandId, url);
}

export async function pollAnalyzeAction(jobId: string): Promise<AnalyzeJobDTO> {
  const { claims, brandId } = await claimsFromSession();
  return pollAnalyze(claims, brandId, jobId);
}
