# User-flow reconciliation: v1 + v2 onboarding behind a server gate

**Date:** 2026-05-19
**Status:** Approved design — ready for implementation plan
**Branch:** `worktree-user-flow-enhancements` (forked from `origin/develop`)

## Goal

Make two journeys the canonical product flows, enforced rather than incidental:

- **Flow 1 (new user):** signup → persona → onboarding chooser → brand onboarding (Quick *or* Manual) → dashboard → signout
- **Flow 2 (returning, onboarded):** signin → dashboard → signout

## Problem

The codebase has signin, persona, a legacy `/onboarding` 5-step form (v1), and a `/onboarding/v2` URL-first AI wizard — but they do not compose:

- Nothing routes to `/onboarding/v2`; persona pushes to `/onboarding?step=1` (v1).
- Only v1 marks onboarding done. `/onboarding/v2`'s completion only calls `router.push("/brand/dashboard")` without setting any flag, so a v2-finishing user bounces back through the funnel.
- "Onboarded" lives only in client mock-session/localStorage — ephemeral and per-browser, so Flow 2 cannot reliably skip the funnel.
- The gate (`RequireOnboarded`) is client-side and carries a documented hydration race (the UAT "click Continue with Google twice" bug).

## Decisions (locked during brainstorming)

1. **Reconciliation shape:** explicit choice. Persona routes to a new `/onboarding` chooser offering **Quick (AI, `/onboarding/v2`)** or **Manual (form, `/onboarding/manual`)**. Both branches end by marking onboarding complete and routing to the dashboard. Both kept as peers behind one gate.
2. **Source of truth:** the backend. cortex-api persists onboarding status; web reads it after login; the gate trusts that response.
3. **Gate placement:** a server-component gate on `/brand/*`, faithful to decision 2 and removing the client hydration race.
4. **`onboarded_at` lives on `brand`** (identity/lifecycle fact), not `brand_profile` (extraction read-shape). This also avoids forcing a junk profile row for the manual branch, which never writes `brand_profile`.
5. **Gate vs. dev bypass:** the server gate honors `NEXT_PUBLIC_DEV_BYPASS_AUTH`. When set, it returns children immediately — no `auth()`, no cortex-api call — mirroring how `MockSessionProvider` already treats the flag as production-dead code.
6. **Gate-failure policy:** never auto-grant onboarded, never redirect-loop. `401/403` → `/error`; `404` → `/onboarding`; `5xx`/network → a retryable error screen.

## Scope

Orchestration plus v1/v2 reconciliation. Screens stay largely as-is; the only new screen is the small chooser. The v1 wizard moves verbatim to a new route.

## Architecture

### The gate

A server component wraps `/brand/*`. On every protected request it decides, in order:

1. dev bypass on → render children (dev-only early return; production-dead)
2. no NextAuth session → `redirect("/signin")`
3. session, no brand `activeContext` → `redirect("/persona")`
4. brand context, `onboarded_at` is NULL → `redirect("/onboarding")`
5. `onboarded_at` set → render the dashboard

The gate lives **only on `/brand/*`**. The `(auth)` routes (signin, persona, onboarding, manual, v2) stay ungated; the gate's job is to bounce *out* of `/brand` when prerequisites are unmet. The forward push persona → `/onboarding` is explicit navigation, not the gate.

Server `redirect()` removes the client hydration race and the `auth-placeholder` flash by construction.

### cortex-api

- **Schema:** add `onboarded_at: datetime | None` (nullable, default `None`) to the `brand` SQLModel in `service/brand_identity/model/brand.py`. NULL means not onboarded. Nullable, so no `server_default` (the CLAUDE.md timestamp rule governs `created_at`/`updated_at`, not this lifecycle stamp). Hand-written Alembic migration, round-tripped up → down → up. No new index — lookups are by `brand.id` PK.
- **`POST /v1/brand/{brand_id}/onboarding/complete`** — branch-agnostic. Stamps `brand.onboarded_at = now()` only if currently NULL (idempotent; second call is a no-op). Capability gate: `EDIT_BRAND_SETTINGS` (mirrors profile PUT; the persona-picker founder holds ADMIN). Returns `{ onboarded_at }`.
- **`GET /v1/brand/{brand_id}/onboarding-status`** — slim, cheap, cacheable. Returns `{ onboarded: bool }`. The server gate calls this. Gated on a read capability the founder holds from brand creation.
- Both endpoints live in `app/api/brand/router.py`; the mutation goes through a `brand_identity` service method that owns the `brand` identity row.

### web

- **Route restructure:**
  - `app/(auth)/onboarding/page.tsx` becomes the **chooser** (Quick → `/onboarding/v2`; Manual → `/onboarding/manual`).
  - The current v1 wizard and its `actions.ts` move verbatim to `app/(auth)/onboarding/manual/`.
  - `app/(auth)/onboarding/v2/` stays.
  - `persona/page.tsx`: `router.push("/onboarding?step=1")` → `router.push("/onboarding")`.
- **Server gate:** split `app/brand/layout.tsx` into a server gate component (`auth()` + `GET …/onboarding-status` + `redirect()`) that renders the existing client shell as its child. Remove `RequireOnboarded` from the brand layout.
- **Branch completion:**
  - Manual: `completeBrandOnboarding` additionally calls `POST …/onboarding/complete` after the brand update, then routes to `/brand/dashboard`.
  - v2: `launchDone`/`handleEnterDiscover` calls a new server action hitting `POST …/onboarding/complete`, then routes to `/brand/dashboard`, replacing the bare `router.push`. Wire this in **both** the EN and zh-TW v2 entry points.
- **Signout:** add an account/sidebar control that calls NextAuth `signOut({ redirectTo: "/signin" })` **and** clears mock-session localStorage. Both — otherwise the client provider re-projects a stale or demo session.

### Deliberate behavior change

Today `mock-session-provider.tsx` sets `onboardingComplete = hasBrandContext ? true`, so the moment persona bakes a brand context the user is treated as onboarded and the wizard is skipped ("deferred-for-MVP, visual only"). This design **intentionally reverses that**: onboarding becomes really enforced via backend `onboarded_at`. State this in the PR so reviewers read it as intent, not regression.

## Data flow

**Flow 1:** `/signin` → Google → `jwt` cb `GET /v1/auth/me` upserts AppUser (no membership → no context) → hits `/brand/*`, gate redirects `/persona` → pick Brand → `createMyBrand` `POST /v1/brand` → client `session.update()` → `jwt` re-resolves, bakes brand `activeContext` → `router.push("/onboarding")` → chooser → Quick or Manual wizard → `POST …/onboarding/complete` stamps `onboarded_at` → `/brand/dashboard` → gate sees `onboarded:true` → dashboard.

**Flow 2:** `/signin` → Google → `jwt` cb finds membership → `resolveContext` bakes brand context → callbackUrl `/brand/dashboard` → gate `GET …/onboarding-status` → `onboarded:true` → dashboard. No funnel. Signout → `/signin`.

**Composition:** a user with a brand membership but NULL `onboarded_at` (abandoned mid-wizard) signs in, reaches `/brand/dashboard`, and the gate redirects to `/onboarding`. Flow 2 degrades into the Flow 1 tail with no separate resume path.

## Error handling

- **Gate status fetch:** `401/403` → `/error` (not `/signin`, to avoid a loop with a valid-but-broken session). `404` (no brand row) → treat as not onboarded → `/onboarding`. `5xx`/network/timeout → retryable error screen reusing the `onboarding/v2` error-card pattern; never redirect, never auto-onboard.
- **`POST …/onboarding/complete` fails:** stay on the wizard, inline error and retry. Do not navigate to `/brand/dashboard` until 2xx — premature navigation triggers an immediate gate bounce-back loop. Idempotency makes retry safe.
- **`createMyBrand` 409** (caller already has a brand): the persona path resolves to the existing brand and proceeds to `/onboarding` rather than dead-ending.
- **Founder lacks the onboarding-status read capability pre-onboarding:** a `BrandCapabilityPolicy` bug, surfaced as `/error`, not swallowed. Open item to verify, written as a test assertion (below).
- NextAuth bootstrap fail-fast → `/error`, unchanged and out of scope.

## Edge cases

- Non-brand `activeContext` on `/brand/*` → gate redirects `/persona`; must not throw. Publisher out of scope.
- Direct deep-link to `/onboarding/manual` or `/onboarding/v2` with no brand context: ungated routes; existing server actions already guard with a descriptive "no active brand context" error. Kept as-is, a known acceptable gap.
- Double completion: endpoint stamps only if NULL; idempotent by construction.
- zh-TW v2 variant: completion wiring applies to both EN and zh-TW v2 entry points.
- Multi-tab signout: NextAuth clears the cookie; mock `signOut` + `notifySameTab` propagates the localStorage clear.

## Testing strategy

- **cortex-api** (override DI providers, not `mock.patch`): `mark_onboarded` idempotency (stamp once, second call no-op); `onboarding-status` true/false and 404 → not onboarded; completion 403 without `EDIT_BRAND_SETTINGS`; Alembic round-trip up → down → up for the `onboarded_at` migration.
- **web:** server-gate decision matrix — no session → `/signin`; no brand context → `/persona`; `onboarded:false` → `/onboarding`; `true` → render; `DEV_BYPASS=true` → render with no `auth()` call; status `5xx` → error screen with no redirect loop. Chooser routes to both branches. Manual and v2 branches call complete then navigate; failure keeps the user on the wizard. Signout calls NextAuth `signOut({redirectTo:"/signin"})` and clears mock localStorage.
- **Test-infra prerequisite:** `mock-session-provider.tsx` notes no vitest jsdom harness exists in `web/`. Bootstrapping that harness is a plan prerequisite for the web gate tests, not an assumption.
- **E2E:** real-Google Playwright for Flow 1/2 is impractical; out of scope unless a test auth seam lands later.

## Open items to resolve during implementation

1. Confirm `BrandCapabilityPolicy` grants the onboarding-status read capability at brand-creation time (before onboarding completes). Encode as a test.
2. Exact module for the `mark_onboarded` mutation (`brand_identity` service, since it mutates the `brand` identity row) — settle when wiring the container.
3. Audit consumers of `useMockSession().onboardingComplete`, `isAuthReady`, and `RequireOnboarded`; the gate signal moves server-side, so the client `onboardingComplete` projection becomes vestigial for gating but may still feed other UI. Do not blanket-delete.

## Out of scope

Publisher onboarding (tables not migrated; PHP owns it). The parallel SP-3b "brandless GTM" workstream that reuses the v2 wizard at `/gtm`. Screen redesign.
