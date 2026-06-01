"use server";

/**
 * Server Actions — media-network pipeline bridge for the onboarding v2 wizard.
 *
 * The `"use client"` wizard cannot call `@/lib/cortex-api` (server-only:
 * imports `cortex-token` which needs `NEXTAUTH_SECRET`). These two thin
 * actions wrap SP-MEDIA's `startMediaNetwork` / `pollMediaNetwork`, deriving
 * `brandId` + signed-token claims from the authenticated NextAuth session
 * server-side so nothing scoping-related is ever trusted from the client.
 *
 * Auth contract mirrors `analyze-actions.ts`: the caller is the founder of a
 * freshly created brand workspace, so they hold an active brand `activeContext`
 * (ADMIN → `EDIT_BRAND_SETTINGS`). Missing session / cortexUserId / active
 * brand context bails with a descriptive error rather than 401-ing inside
 * cortex-api.
 */

import { auth } from "@/lib/auth";
import { type MediaNetworkDTO, pollMediaNetwork, startMediaNetwork } from "@/lib/cortex-api";
import type { CortexTokenClaims } from "@/lib/cortex-token";

async function claimsFromSession(): Promise<{ claims: CortexTokenClaims; brandId: string }> {
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

export async function startMediaNetworkAction(): Promise<MediaNetworkDTO> {
  const { claims, brandId } = await claimsFromSession();
  return startMediaNetwork(claims, brandId);
}

export async function pollMediaNetworkAction(): Promise<MediaNetworkDTO> {
  const { claims, brandId } = await claimsFromSession();
  return pollMediaNetwork(claims, brandId);
}
