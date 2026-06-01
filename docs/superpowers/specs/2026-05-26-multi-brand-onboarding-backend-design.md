# Multi-brand onboarding — backend enablement (slice 1)

**Status:** approved (Okis, 2026-05-26). Autonomous implementation authorized.

## Goal
Make brand creation **always create a new, independent brand** so the onboarding flow can be multi-brand. Each onboarding run yields its own `brand_id` with its own profile + derived data and **never overrides** another brand. This slice is **backend/data-model only**.

## Decision context
- Product decision (2026-05-26): onboarding = create-new-brand always; editing an existing brand is a separate explicit flow (later); no override of other brands.
- The server already supports multi-brand *membership* (`auth/me` lists all memberships; auth router has `enter_brand` + `resolve-context` to switch active context). The **only blocker** is the founder-uniqueness DB constraint that 409s a 2nd brand.

## In scope
1. **Drop** the `brand_membership_founder_uniq` partial unique index (`brand_membership(user_id) WHERE invited_by IS NULL`, from migration `a1f4c8d2e3b5`) via a new Alembic migration (down_revision = `a2b3c4d5e6f7`, current head). `downgrade()` re-creates it. Round-trip safe.
2. **`create_brand_with_admin`** (`api/src/cortex_api/service/brand_identity/service.py`): remove the `IntegrityError → ConflictError("…already has a founder membership…")` branch. Always create `Brand` + ADMIN `BrandMembership(invited_by=None)`. Update the docstring (no longer "one founder per user"). The `UniqueConstraint(user_id, brand_id)` stays (no duplicate membership in the *same* brand).
3. **Tests**: replace the "2nd founder brand → 409/Conflict" test with "a user can create multiple independent brands, each with its own ADMIN membership"; add migration round-trip coverage.

## Out of scope (later slices)
- "Add/create another brand" UI entry point.
- Brand switcher in the shell.
- `RequireOnboarded` gate revision for returning users.
- Separate edit-existing-brand flow (+ its idempotent regenerate-derived-results rule).

## Why this is safe to ship now (dormant capability)
No UI path triggers a 2nd-brand creation yet (entry deferred), so the dropped index + the code change are dormant: existing single-brand users are unaffected, and there is no live path that could hit a half-applied state. Deploy/migration order is therefore non-critical.

## Risk
- Dropping an index is non-data-destructive and reversible (downgrade re-creates). It removes the TOCTOU guard against concurrent first sign-ins creating duplicate brands; acceptable because (a) no UI path triggers repeated creation yet and (b) duplicate-prevention on rapid submit belongs to the future UI entry.

## Verification
- `pytest` unit + integration (incl. brand_identity create-multiple-brands); migration round-trip (`upgrade head → downgrade -1 → upgrade head`); `ruff` + `mypy` clean; `make lint`.
- UAT: apply the migration to RDS (manual — no CI/helm migration step), deploy code, confirm pods healthy + index dropped.
