"use client";

import { signIn } from "next-auth/react";

import { Button } from "@/components/ui/button";

/**
 * "Continue with Google" — kicks off real Google OAuth via NextAuth.
 *
 * After Google consent, NextAuth's jwt callback enriches the token via
 * cortex-api (`/v1/auth/me` + `/v1/auth/resolve-context` — see
 * `src/lib/auth.ts`), then redirects to `callbackUrl` (`/`). The root
 * page reads the session and routes:
 *   - no `activeContext` → `/persona` (persona picker)
 *   - has `activeContext` → `/brand/dashboard`
 *
 * The previous mock-session signIn flow is gone — see
 * `project_cortex_mvp.md` § Onboarding flow design.
 */
export function SignInButton() {
  return (
    <Button
      type="button"
      variant="dark"
      className="h-12 w-full gap-2.5 text-[15px]"
      onClick={() => {
        void signIn("google", { callbackUrl: "/" });
      }}
    >
      <span
        className="material-icons-outlined"
        style={{ fontSize: 18 }}
        aria-hidden
      >
        login
      </span>
      Continue with Google
    </Button>
  );
}
