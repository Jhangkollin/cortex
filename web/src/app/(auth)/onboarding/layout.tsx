import "server-only";

import { redirect } from "next/navigation";

import { auth } from "@/lib/auth";

/**
 * Auth guard for the `/onboarding/*` namespace (chooser, v2 + v2/zh-TW,
 * manual). Server-rendered before any child page's client bundle ships, so
 * unauthenticated visitors that deep-link here are bounced to `/signin`
 * without the protected wizard JS ever reaching their browser.
 *
 * Narrower than `OnboardingGate`: only a session is required. The fuller
 * ladder (no brand context → /persona, not onboarded → /onboarding) would
 * bounce the very users these pages exist to serve.
 *
 * Dev bypass mirrors `OnboardingGate` so local dev with
 * `NEXT_PUBLIC_DEV_BYPASS_AUTH=true` is unaffected.
 */
export default async function OnboardingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  if (process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === "true") {
    return <>{children}</>;
  }

  const session = await auth();
  if (!session?.user) {
    redirect("/signin");
  }

  return <>{children}</>;
}
