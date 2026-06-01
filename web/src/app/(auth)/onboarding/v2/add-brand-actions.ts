"use server";

/**
 * Server Action — create another brand in the user's portfolio (multi-brand).
 *
 * Wraps `createBrand` (cortex-api). Returns the new brand's id and the
 * `activeContext` shape the client needs to pass to `useSession().update()`
 * so the JWT carries the new brand_id on its next callback. The wizard's
 * server actions read `claims.activeContext.id`, so refreshing it on the
 * client BEFORE navigating to `/onboarding/v2` is what makes the next run
 * operate on the new brand instead of overwriting the previous one.
 */

import { auth } from "@/lib/auth";
import { createBrand, listMyBrands, type ActiveContextResponse, type BrandListItem } from "@/lib/cortex-api";
import type { CortexTokenClaims } from "@/lib/cortex-token";

export async function createAnotherBrandAction(): Promise<{
  brandId: string;
  activeContext: ActiveContextResponse;
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

  const claims: CortexTokenClaims = {
    cortexUserId: session.user.cortexUserId,
    email: session.user.email,
    displayName: session.user.name ?? null,
    // createBrand derives the calling user from cortexUserId, not the
    // active brand — any valid activeContext satisfies the type. Use the
    // current session's one if present.
    activeContext: session.user.activeContext,
  };

  const result = await createBrand(claims);
  const newCtx: ActiveContextResponse = {
    kind: "brand",
    id: result.brand.id,
    role: result.role,
    capabilities: result.capabilities,
  };
  return { brandId: result.brand.id, activeContext: newCtx };
}

export async function listMyBrandsAction(): Promise<BrandListItem[]> {
  const session = await auth();
  if (!session?.user?.email || !session.user.cortexUserId) return [];
  const claims: CortexTokenClaims = {
    cortexUserId: session.user.cortexUserId,
    email: session.user.email,
    displayName: session.user.name ?? null,
    activeContext: session.user.activeContext,
  };
  try {
    return await listMyBrands(claims);
  } catch {
    return [];
  }
}
