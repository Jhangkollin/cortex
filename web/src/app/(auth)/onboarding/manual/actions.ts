"use server";

/**
 * Server Action — final step of the 5-step onboarding wizard.
 *
 * Persists only the brand display name from the wizard draft via
 * `PATCH /v1/brand/{brand_id}`. Every other wizard field (shortName,
 * primaryDomain, altDomains, industry, contact*, placement topics) is
 * intentionally NOT written — the demo-time scope is "rename the brand
 * from 'Untitled' to whatever the user typed in step 1, leave the rest
 * visual." A future slice will land a `brand_profile` table to hold the
 * deferred fields properly.
 *
 * Auth: the caller is the founder of this brand workspace (just created
 * via the persona picker), so they hold ADMIN → `EDIT_BRAND_SETTINGS`.
 * If somehow they hit step 5 without an active_context (e.g. session
 * corruption between persona → onboarding), the action bails with a
 * descriptive error rather than silently 401-ing inside cortex-api.
 */

import { auth } from "@/lib/auth";
import {
  completeOnboarding,
  updateBrand,
  type UpdateBrandBody,
} from "@/lib/cortex-api";
import type { OnboardingDraft } from "@/lib/mock-session";

interface CompleteBrandOnboardingResult {
  brandId: string;
  brandDisplayName: string;
}

export async function completeBrandOnboarding(
  draft: OnboardingDraft,
): Promise<CompleteBrandOnboardingResult> {
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

  const body: UpdateBrandBody = {};
  const displayName = draft.companyName?.trim();
  if (displayName) body.display_name = displayName;

  // Shared by both cortex-api calls below — extracted so the two call
  // sites can't silently diverge if one is later edited.
  const claims = {
    cortexUserId: session.user.cortexUserId,
    email: session.user.email,
    displayName: session.user.name ?? null,
    activeContext,
  };

  const brand = await updateBrand(claims, activeContext.id, body);

  await completeOnboarding(claims, activeContext.id);

  return {
    brandId: brand.id,
    brandDisplayName: brand.display_name,
  };
}
