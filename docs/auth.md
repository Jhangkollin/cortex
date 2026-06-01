# Auth flow

NextAuth (in `cortex-web`) handles the Google OAuth dance. Cortex-api verifies the resulting JWT locally with the shared `NEXTAUTH_SECRET`.

```
Browser → cortex-web /signin
          NextAuth → Google OAuth consent
          Google returns code → NextAuth exchanges for tokens
          signIn callback: profile.email must end in @mlytics.com
          NextAuth signs JWT, sets httpOnly cookie

Browser → cortex-web /brand/dashboard (RSC)
          auth() helper validates session, prefetches data
          API requests forward the JWT as Authorization: Bearer <token>

cortex-api authenticated_user dependency
          decode + verify with NEXTAUTH_SECRET (HS256)
          return AuthedUser

cortex-api active_brand / active_publisher dependency
          read active_context from JWT
          assert context kind matches the route
          assert context id matches the URL id
          return BrandTenantCtx / PublisherTenantCtx

cortex-api capability dependency
          check required capability from active_context.capabilities
```

## Bootstrap vs session token shapes

cortex-web signs **two** distinct JWT shapes for cortex-api. Cortex-api's `current_app_user` dep (`api/src/cortex_api/app/dependencies/auth.py`) dispatches on the `token_kind` claim:

| `token_kind` | When minted | `sub` carries | Required extra claim | Optional claims | cortex-api action |
|---|---|---|---|---|---|
| `"bootstrap"` | NextAuth `jwt` callback on first-ever sign-in, BEFORE the AppUser UUID is known | UUIDv5 placeholder derived from `oauth_subject` (syntactic concession — `authenticated_user` parses `sub` as a UUID) | `oauth_subject` (Google numeric subject) | `display_name` (Google profile name; omitted when null/empty so the JSON stays clean) | `recognize_user(oauth_subject=..., display_name=...)` — upserts AppUser by Google subject, refreshes `display_name` from the latest claim |
| `"session"` | Every subsequent call (`signCortexApiToken`) once the AppUser UUID has been resolved | App user UUID (the real identity) | — | `display_name`, `active_context` | `get_user(sub)` — fetches AppUser by primary key |
| missing / any other value | — | — | — | — | `UnauthorizedError` (401) — fail-fast at the boundary |

The signers live in `web/src/lib/cortex-token.ts`:

- `signBootstrapToken(oauthSubject, email, displayName?)` — stamps `token_kind: "bootstrap"` + `oauth_subject`. When `displayName` is non-null/non-empty it is included as a `display_name` claim so cortex-api can populate `app_user.display_name` on first sign-in (otherwise the column would stay `NULL` and downstream UI would show "Untitled brand").
- `signCortexApiToken({ cortexUserId, ... })` — stamps `token_kind: "session"`.

**Why the explicit claim, not a heuristic?** Earlier revisions branched on `"oauth_subject" in claims`, which silently mishandled drift cases (e.g. an old cookie that still had `oauth_subject` but pointed at a stale Google id). The named claim makes the contract symmetric across both repos and 401s on misconfiguration instead of hitting the wrong branch.

Any change to this contract must be reflected in **both** `current_app_user` (Python) and the cortex-token signers (TypeScript) — there is no shared schema enforcing it.

## Settings

| Where | Var | Purpose |
|---|---|---|
| cortex-web | `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth app credentials |
| cortex-web | `NEXTAUTH_SECRET` | JWT signing secret (shared with cortex-api) |
| cortex-web | `NEXTAUTH_ALLOWED_DOMAIN` | Default `mlytics.com` |
| cortex-api | `CORTEX_AUTH_JWT_SECRET` | Same value as `NEXTAUTH_SECRET` |
| cortex-api | `CORTEX_AUTH_JWT_ALGORITHM` | `HS256` |
| cortex-api | `CORTEX_AUTH_JWT_AUDIENCE` | `cortex-api` |

## When something fails

| Symptom | Likely cause |
|---|---|
| Google sign-in succeeds but redirect to `/error` | email isn't `@mlytics.com` |
| API returns 401 on every call | JWT signature mismatch — secrets diverged between web and api |
| API returns 403 with "MembershipError" | user has no membership in the requested Brand/Publisher context |
| API returns 400 with "ContextMismatchError" | Existing `core/exceptions.py` error for JWT `active_context.id` not matching the route id |
