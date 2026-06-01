"use server";

/**
 * Server Action — persona-picker submission for "Brand Customer".
 *
 * Reads the current NextAuth session, signs an ephemeral JWS for cortex-api
 * server-side, calls `POST /v1/brand` which atomically creates the brand +
 * ADMIN membership for the caller (or returns 409 if they already have one).
 * Returns the new brand id; the client then triggers `session.update()` so
 * NextAuth's `jwt` callback re-resolves the active_context and bakes it
 * into the next session token.
 */

import { auth } from "@/lib/auth";
import { createBrand } from "@/lib/cortex-api";

interface CreateMyBrandResult {
  brandId: string;
  brandDisplayName: string;
}

export async function createMyBrand(): Promise<CreateMyBrandResult> {
  const session = await auth();
  if (!session?.user?.email) {
    throw new Error("Not signed in");
  }
  if (!session.user.cortexUserId) {
    // Defense-in-depth: post fail-fast, a successful sign-in always has
    // cortexUserId. If it's missing here, the session predates the
    // fail-fast change OR something else corrupted the token. Friendly
    // error pointing at the recovery action.
    throw new Error(
      "Sign-in did not complete. Please sign out and sign in again.",
    );
  }

  const result = await createBrand({
    cortexUserId: session.user.cortexUserId,
    email: session.user.email,
    displayName: session.user.name ?? null,
    activeContext: session.user.activeContext,
  });

  return {
    brandId: result.brand.id,
    brandDisplayName: result.brand.display_name,
  };
}
