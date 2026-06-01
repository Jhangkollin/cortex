/**
 * NextAuth configuration — Google OAuth + cortex-api enrichment.
 *
 * Exports the `auth()` helper for Server Components, plus the route handlers
 * mounted at `/api/auth/[...nextauth]/route.ts`.
 *
 * Pattern B JWT (see `project_cortex_mvp.md` § Onboarding flow design):
 * - NextAuth signs ALL session tokens (JWE-encrypted httpOnly cookie).
 * - On first sign-in, the `jwt` callback calls cortex-api `GET /v1/auth/me`
 *   to upsert the AppUser and discover memberships. If a default membership
 *   is available, it then calls `POST /v1/auth/resolve-context` to bake the
 *   role + capabilities into the token under `activeContext`.
 * - On `trigger: "update"` (called from Server Actions / client after the
 *   persona picker creates a brand), the callback re-resolves and updates
 *   `activeContext` in-place.
 *
 * cortex-api NEVER mints a JWT — it only verifies signatures and resolves
 * capabilities on demand. Browser JS never sees the cortex-api access
 * token (ephemeral JWS, signed server-side per request — see
 * `src/lib/cortex-token.ts`).
 *
 * ⚠️ Domain allowlist below currently restricts sign-in to `@mlytics.com`.
 * Correct for internal pilots; lift the gate when real customer onboarding
 * lands. See task IR / cortex go-live decisions memory.
 */

import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

import { fetchMeWithBootstrap, resolveContext } from "@/lib/cortex-api";

const allowedDomain = process.env.NEXTAUTH_ALLOWED_DOMAIN ?? "mlytics.com";

/**
 * Canonical "where does the user's display name come from" resolver.
 *
 * Fallback priority: NextAuth `user.name` → OAuth `profile.name` →
 * persisted `token.name` (set by an earlier bootstrap pass).
 *
 * Each call site passes whichever sources are in scope at that point in
 * the jwt callback — bootstrap has all three, trigger:"update" only has
 * `token`. Centralising this here avoids the divergence that caused the
 * 2026-05-13 "Untitled brand" bug class (three sites, three different
 * fallback chains, silent inconsistency).
 */
function pickDisplayName(
  ...candidates: Array<string | null | undefined>
): string | null {
  for (const c of candidates) {
    if (typeof c === "string" && c.length > 0) return c;
  }
  return null;
}

function asString(v: unknown): string | null {
  return typeof v === "string" && v.length > 0 ? v : null;
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    }),
  ],
  pages: {
    signIn: "/signin",
    error: "/error",
  },
  trustHost: true,
  // Behind the TLS-terminating ALB the pod sees `http`, so Auth.js v5's
  // request-protocol auto-detection sets the transient OAuth cookies
  // inconsistently (prefix / `secure` flag) between the authorize leg and
  // the callback leg. Across 2 cortex-web replicas with no sticky sessions
  // the two legs land on different pods and the verifier cookie no longer
  // matches → `InvalidCheck: pkceCodeVerifier value could not be parsed`,
  // which bounces the user to the misleading "Sign-in failed" page and
  // blocks BOTH signup and signin. Pin these cookies explicitly so the
  // name + `secure` flag are identical on every leg regardless of the
  // protocol the pod thinks it saw. Scoped to the short-lived OAuth
  // round-trip cookies only — sessionToken/csrf/callbackUrl keep Auth.js
  // defaults so existing logged-in sessions are NOT invalidated. The
  // browser↔ALB hop is HTTPS, so `__Secure-` + `secure: true` is valid.
  cookies: {
    pkceCodeVerifier: {
      name: "__Secure-authjs.pkce.code_verifier",
      options: {
        httpOnly: true,
        sameSite: "lax",
        path: "/",
        secure: true,
        maxAge: 900,
      },
    },
    state: {
      name: "__Secure-authjs.state",
      options: {
        httpOnly: true,
        sameSite: "lax",
        path: "/",
        secure: true,
        maxAge: 900,
      },
    },
    nonce: {
      name: "__Secure-authjs.nonce",
      options: {
        httpOnly: true,
        sameSite: "lax",
        path: "/",
        secure: true,
      },
    },
  },
  callbacks: {
    async signIn({ profile }) {
      const email = profile?.email;
      if (!email) return false;
      if (!email.endsWith(`@${allowedDomain}`)) return false;
      return true;
    },

    async jwt({ token, user, account, profile, trigger, session }) {
      // First sign-in: `account` and `profile` are set. Call cortex-api to
      // upsert the AppUser and pick a default active context (if any).
      //
      // Fail-fast: bootstrap failure rejects the sign-in entirely. There
      // is no degraded UI here — without `cortexUserId` on the session,
      // every Server Action / API call would fail anyway, so we'd rather
      // surface the real error at /error than ship the user into a UI
      // that 500s on every click. The error propagates to NextAuth which
      // redirects to `pages.error` (/error).
      if (account && profile && user?.email) {
        const oauthSubject = String(profile.sub ?? account.providerAccountId);
        // Resolve display_name ONCE per bootstrap; persist on the token so
        // every subsequent trigger:"update" sees the same value. Forwarding
        // to cortex-api populates app_user.display_name on first sign-in
        // (otherwise downstream brand auto-naming falls back to "Untitled
        // brand").
        const displayName = pickDisplayName(
          user.name,
          asString((profile as { name?: unknown }).name),
        );
        token.email = user.email;
        if (displayName) token.name = displayName;

        const me = await fetchMeWithBootstrap(oauthSubject, user.email, displayName);
        token.cortexUserId = me.user_id;
        if (me.memberships.length > 0) {
          // Bake the first membership as the default active context.
          // (Multi-membership picker = future work; until then "first" is fine.)
          const m = me.memberships[0];
          const ctx = await resolveContext(
            {
              cortexUserId: me.user_id,
              email: user.email,
              displayName,
            },
            m.kind,
            m.id,
          );
          token.activeContext = ctx;
        }
      }

      // Context switch: caller invoked `session.update({...})` from a
      // Server Action (typically the persona picker after `POST /v1/brand`).
      // The new context fields arrive on `session` and we re-resolve to
      // pick up server-side capability changes.
      const cortexUserId = token.cortexUserId as string | undefined;
      if (trigger === "update" && session && token.email && cortexUserId) {
        const next = (session as Record<string, unknown>).activeContext as
          | { kind: "brand" | "publisher"; id: string }
          | undefined;
        if (next?.kind && next.id) {
          try {
            const ctx = await resolveContext(
              {
                cortexUserId,
                email: token.email as string,
                displayName: pickDisplayName(asString(token.name)),
              },
              next.kind,
              next.id,
            );
            token.activeContext = ctx;
          } catch (err) {
            console.error("[auth.jwt update] resolve-context failed:", err);
          }
        }
      }

      return token;
    },

    async session({ session, token }) {
      if (token.email) session.user.email = token.email as string;
      const cortexUserId = token.cortexUserId as string | undefined;
      if (cortexUserId) session.user.cortexUserId = cortexUserId;
      const activeContext = token.activeContext as
        | {
            kind: "brand" | "publisher";
            id: string;
            role: string;
            capabilities: string[];
          }
        | undefined;
      if (activeContext) session.user.activeContext = activeContext;
      return session;
    },
  },
  session: { strategy: "jwt" },
});

export const { GET, POST } = handlers;
