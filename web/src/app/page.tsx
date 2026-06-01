/**
 * Root landing — Server Component, routes post-OAuth callbacks.
 *
 *   no session                       → /signin
 *   session but no activeContext     → /persona
 *   session with activeContext       → /brand/dashboard
 *
 * NextAuth's jwt callback fills `activeContext` automatically when the
 * user already has a brand membership (see `src/lib/auth.ts`). First-time
 * users land here with no `activeContext` and get routed to the persona
 * picker, which calls cortex-api `POST /v1/brand` to create one.
 */

import { redirect } from "next/navigation";

import { auth } from "@/lib/auth";

export default async function HomePage() {
  if (process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === "true") {
    redirect("/brand/dashboard");
  }

  const session = await auth();

  if (!session?.user) {
    redirect("/signin");
  }

  if (!session.user.activeContext) {
    redirect("/persona");
  }

  redirect("/brand/dashboard");
}
