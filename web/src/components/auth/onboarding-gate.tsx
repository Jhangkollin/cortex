import "server-only";

import { redirect } from "next/navigation";

import { auth } from "@/lib/auth";
import { getOnboardingStatus, OnboardingStatusError } from "@/lib/cortex-api";

/**
 * "render" / "retry" sentinels, or one of the closed set of internal routes
 * the gate redirects to. Kept as an explicit literal union (not `string`)
 * so `redirect()` type-checks under Next's `typedRoutes` without a cast and
 * the gate can never redirect to an unknown route.
 */
export type GateDestination =
  | "render"
  | "retry"
  | "/signin"
  | "/persona"
  | "/onboarding"
  | "/error";

/**
 * Pure decision function (unit-testable). Returns "render", "retry", or one
 * of the closed set of redirect routes. Never throws for control flow.
 *
 * Decision ladder (order is load-bearing — see CLAUDE.md authz spine):
 *   dev-bypass → no session → /signin → no brand ctx → /persona →
 *   not onboarded → /onboarding → onboarded → render.
 *
 * `NEXT_PUBLIC_DEV_BYPASS_AUTH` is read per-call (first line, not a
 * module-scope const) so the value is observed deterministically under
 * test. Production never sets this env var, so
 * `process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === "true"` is statically false
 * there: Next.js inlines `NEXT_PUBLIC_*` at build time and
 * dead-code-eliminates this guard — the bypass branch ships only in dev.
 */
export async function resolveGateDestination(): Promise<GateDestination> {
  if (process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === "true") return "render";

  const session = await auth();
  if (!session?.user?.email) return "/signin";

  const ctx = session.user.activeContext;
  if (!ctx || ctx.kind !== "brand" || !ctx.id) return "/persona";

  try {
    const status = await getOnboardingStatus(
      {
        cortexUserId: session.user.cortexUserId ?? "",
        email: session.user.email,
        displayName: session.user.name ?? null,
        activeContext: ctx,
      },
      ctx.id,
    );
    return status.onboarded ? "render" : "/onboarding";
  } catch (e) {
    if (e instanceof OnboardingStatusError) {
      if (e.status === 401 || e.status === 403) return "/error";
      if (e.status === 404) return "/onboarding";
    }
    return "retry";
  }
}

export async function OnboardingGate({
  children,
}: {
  children: React.ReactNode;
}) {
  const dest = await resolveGateDestination();
  if (dest === "render") return <>{children}</>;
  if (dest === "retry") {
    return (
      <div
        role="alert"
        className="flex min-h-screen items-center justify-center bg-ink-25"
      >
        <div className="w-full max-w-sm space-y-2 p-8 text-center">
          <p className="text-base font-semibold">
            Couldn&apos;t check your workspace
          </p>
          <p className="text-sm text-ink-500">
            Nothing was lost — reload to try again.
          </p>
          <a
            href="/brand/dashboard"
            className="inline-block pt-2 text-sm font-medium text-ink-500 underline"
          >
            Go to dashboard
          </a>
        </div>
      </div>
    );
  }
  // `redirect` throws by design to abort the render — only ever reached for
  // a path destination, never "render"/"retry".
  redirect(dest);
}
