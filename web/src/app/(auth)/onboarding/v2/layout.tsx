import { redirect } from "next/navigation";

import { auth } from "@/lib/auth";
import { getOnboardingStatus } from "@/lib/cortex-api";
import type { CortexTokenClaims } from "@/lib/cortex-token";

/**
 * Safety rail: refuse to run the v2 wizard against an already-onboarded
 * brand.
 *
 * Without this, navigating to /onboarding/v2 with an active_context pointing
 * at an onboarded brand would silently overwrite that brand's profile
 * (because every wizard server-action reads activeContext.id from the
 * session). The chunk-3 "Add a brand" entry creates a new brand AND refreshes
 * the session before navigating — but direct navigation is the foot-gun this
 * layout closes.
 */
export default async function OnboardingV2Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();
  const activeContext = session?.user?.activeContext;
  if (
    !session?.user?.email ||
    !session.user.cortexUserId ||
    !activeContext ||
    activeContext.kind !== "brand" ||
    !activeContext.id
  ) {
    redirect("/onboarding");
  }

  const claims: CortexTokenClaims = {
    cortexUserId: session.user.cortexUserId,
    email: session.user.email,
    displayName: session.user.name ?? null,
    activeContext,
  };
  try {
    const status = await getOnboardingStatus(claims, activeContext.id);
    if (status.onboarded) {
      // Active brand is already onboarded — bounce to the chooser, which
      // surfaces "Add another brand" as the explicit non-destructive entry.
      redirect("/onboarding");
    }
  } catch (err) {
    // Fail-open: a blocked wizard on a transient network blip is worse UX
    // than a rare overwrite. Log so operators can spot a flapping API.
    console.warn("[onboarding-v2/layout] safety-rail check failed, failing open", err);
  }

  return <>{children}</>;
}
