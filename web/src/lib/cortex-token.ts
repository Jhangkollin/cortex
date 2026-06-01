/**
 * Server-only ephemeral JWS signer for cortex-api calls.
 *
 * **Never import this from a Client Component** — `NEXTAUTH_SECRET` would
 * leak into the browser bundle. Importing from Server Components, Server
 * Actions, and Route Handlers is fine.
 *
 * Why ephemeral: NextAuth signs session cookies as JWE (encrypted with
 * A256CBC-HS512). cortex-api verifies HS256 JWS. Rather than store a
 * pre-signed cortex-api token anywhere, we mint one on demand (60s TTL)
 * per server-side request, using fields read out of the current NextAuth
 * session. The browser JS never sees the cortex-api token — XSS surface
 * is minimal.
 */

import { SignJWT } from "jose";
import { v5 as uuidv5 } from "uuid";

import type { Session } from "next-auth";

const ALG = "HS256";
const AUDIENCE = "cortex-api";
const ISSUER = "cortex-web";

/**
 * Stable namespace UUID for cortex bootstrap-token `sub` placeholders.
 *
 * cortex-api's `Depends(authenticated_user)` calls `UUID(claims["sub"])`
 * unconditionally, so the bootstrap token (minted BEFORE we know the
 * AppUser's UUID) needs a UUID-shaped value in `sub`. We derive a
 * deterministic UUIDv5 from the Google `oauth_subject` under this
 * namespace — same Google id always maps to the same placeholder UUID
 * within a session, but the real AppUser identity lookup is keyed on the
 * `oauth_subject` claim, not on `sub`.
 *
 * Hardcoded UUIDv4 picked once — do not rotate; if rotated, in-flight
 * bootstrap tokens already minted under the old namespace would still
 * verify (the namespace is opaque to the api), so the only risk is
 * developer confusion when comparing two minted tokens.
 */
const BOOTSTRAP_NAMESPACE = "5f7d3a6e-1c4b-4b9c-9a8e-2e5f0b9b1d3c";

let cachedSecret: Uint8Array | null = null;

function getSecret(): Uint8Array {
  if (cachedSecret) return cachedSecret;
  const raw = process.env.NEXTAUTH_SECRET;
  if (!raw) {
    throw new Error(
      "NEXTAUTH_SECRET missing — cortex-api token signing requires it. " +
        "Set in cortex-rds-credentials Secret (via the helm chart) or local .env.",
    );
  }
  cachedSecret = new TextEncoder().encode(raw);
  return cachedSecret;
}

/**
 * Cortex-api expects every JWT to carry a `token_kind` claim — see
 * `docs/auth.md` § "Bootstrap vs session token shapes". The `current_app_user`
 * dep on the api side dispatches on this value:
 *
 * - `"bootstrap"` — minted by `signBootstrapToken`. Carries Google
 *   `oauth_subject`; api upserts AppUser by it.
 * - `"session"`   — minted by `signCortexApiToken`. `sub` IS the app_user
 *   UUID resolved on a prior bootstrap call.
 *
 * Missing/unknown values 401 at the boundary, so adding a new shape requires
 * a coordinated edit on both sides.
 */
export interface CortexTokenClaims {
  /** App user UUID resolved by cortex-api at sign-in (NOT the Google sub). */
  cortexUserId: string;
  email: string;
  displayName?: string | null;
  /**
   * Active brand/publisher context if the user has resolved one. Absent on
   * first-ever sign-in (persona-picker path); cortex-api's
   * `Depends(active_brand)` will reject those calls — that's fine for
   * `/v1/auth/me` and `POST /v1/brand` which don't require active_context.
   */
  activeContext?: {
    kind: "brand" | "publisher";
    id: string;
    role: string;
    capabilities: string[];
  };
}

/**
 * Sign an HS256 JWS valid for 60s, payload shaped for cortex-api's
 * `Depends(authenticated_user)` and (optionally) `Depends(active_brand)`.
 *
 * Stamps `token_kind: "session"` so cortex-api's `current_app_user` dep
 * fetches the AppUser by `sub` (the app_user UUID) instead of running the
 * bootstrap upsert path.
 */
export async function signCortexApiToken(
  claims: CortexTokenClaims,
): Promise<string> {
  const payload: Record<string, unknown> = {
    sub: claims.cortexUserId,
    email: claims.email,
    token_kind: "session",
  };
  if (claims.displayName) payload.display_name = claims.displayName;
  if (claims.activeContext) payload.active_context = claims.activeContext;

  return await new SignJWT(payload)
    .setProtectedHeader({ alg: ALG })
    .setIssuedAt()
    .setIssuer(ISSUER)
    .setAudience(AUDIENCE)
    .setExpirationTime("60s")
    .sign(getSecret());
}

/**
 * Sign a token from a NextAuth session. Returns `null` if the session
 * doesn't yet have a cortex user id (which means cortex-api hasn't been
 * called yet for this user — caller should run `/v1/auth/me` first via
 * a temp token derived from the bare email instead).
 */
export async function signCortexApiTokenFromSession(
  session: Session | null,
): Promise<string | null> {
  if (!session?.user?.email) return null;
  const cortexUserId = session.user.cortexUserId;
  if (!cortexUserId) return null;
  return signCortexApiToken({
    cortexUserId,
    email: session.user.email,
    displayName: session.user.name ?? null,
    activeContext: session.user.activeContext,
  });
}

/**
 * Sign a "bootstrap" token used by NextAuth's `jwt` callback BEFORE
 * cortex-api has been called for the first time.
 *
 * Token shape:
 * - `sub` — a deterministic UUIDv5 placeholder derived from
 *   `oauthSubject`. This is purely a syntactic concession: cortex-api's
 *   `authenticated_user` dep parses `sub` as a UUID and 401s on
 *   anything else (e.g. Google's numeric id like `"104895824..."`).
 *   The placeholder is NEVER the AppUser identity.
 * - `oauth_subject` — the real Google OAuth subject. cortex-api's
 *   `/v1/auth/me` and `POST /v1/brand` upsert / look up the AppUser by
 *   reading this claim (see `app/api/auth/router.py`).
 * - `display_name` (optional) — the Google profile name. cortex-api
 *   forwards this into `recognize_user` so `app_user.display_name` is
 *   populated on first sign-in (otherwise NULL → downstream "Untitled
 *   brand" cosmetic bug). Omitted from the JWT entirely when null/empty
 *   so the claim set stays clean.
 * - `token_kind: "bootstrap"` — explicit marker for log triage.
 *
 * After the first `/v1/auth/me` call returns the AppUser UUID, the
 * callback should switch to `signCortexApiToken(...)` for subsequent
 * calls, where `sub` carries the real AppUser id.
 */
export async function signBootstrapToken(
  oauthSubject: string,
  email: string,
  displayName?: string | null,
): Promise<string> {
  const payload: Record<string, unknown> = {
    sub: uuidv5(oauthSubject, BOOTSTRAP_NAMESPACE),
    email,
    oauth_subject: oauthSubject,
    token_kind: "bootstrap",
  };
  if (displayName) payload.display_name = displayName;

  return await new SignJWT(payload)
    .setProtectedHeader({ alg: ALG })
    .setIssuedAt()
    .setIssuer(ISSUER)
    .setAudience(AUDIENCE)
    .setExpirationTime("60s")
    .sign(getSecret());
}
