# SP-1 — Brand Profile Write Model + Persistence — Design

- **Date:** 2026-05-18
- **Status:** Approved (brainstorming) — ready for implementation planning
- **Scope:** SP-1 of the Brand Onboarding program. Covers **only** the brand-profile write model and its persistence path.

## Context

SP-1 is the persistence foundation of the four-spike brand-onboarding
decomposition. SP-2 (`cortex-brand-extract`) already extracts a `BrandProfile`
(PR #28). SP-1 makes that profile **durably land in Postgres, tenant-scoped**,
behind a real cortex-api endpoint, so SP-3 can read and write it.

| Spike | Status |
|---|---|
| **SP-1** — brand profile write model + persistence (this spec) | designing |
| SP-2 — extraction engine | done (PR #28) |
| SP-3 — two-mode engine + GTM surface + `HttpOnboardingApi` projection | not started |
| SP-4 — Brand Insight one-pager | not started |

### Grounded reality

- **Identity is real and migrated:** `app_user`, `brand` (UUID v7 PK,
  `display_name`/`industry`/`domain`/`archived_at`/timestamps),
  `brand_membership` (+ `brandrole` enum, founder partial-unique). The auth
  spine works zero-DB: JWT → `AuthedUser` → `BrandTenantCtx`, with
  `active_brand` and `requires_brand_capability` FastAPI deps.
- **The brand-profile scaffold is stubbed and mis-keyed:**
  `service/brand/model/profile.py` exists but FKs a phantom `org.id` (int) —
  there is no `org` table. Repos and service raise `NotImplementedError`. The
  write router is 501. `BrandContainer` is not instantiated in `main.py`. The
  brand models are absent from `alembic/env.py` autogenerate.
- **SP-2 shape to persist a subset of:** `BrandProfile{url, name, legal_name?,
  tagline?, monogram?, brand_color?, category{value,confidence,alternatives},
  region[], founded?, about?, voice_samples[], products[], competitors[],
  media_matches[], extraction_meta}`.

## Locked decisions

1. **Scope — full vertical slice, `brand_profile` only.** Deliver schema +
   migration + repo + service + real `GET`/`PUT /v1/brand/{brand_id}/profile`
   + DI wiring + seed. `contract` / `kb_source` / `reference_answer` stay
   stubbed (Placement/Agent domains, not brand-profile persistence).
2. **Identity FK — `brand.id` (UUID v7), forward-compatible.** `brand_profile`
   keys to the shipped MVP `brand.id`, correcting the dead `org_id:int`
   scaffold. A documented invariant — `brand_profile.brand_id` equals the
   future `org.id` when Org convergence happens — and brand-agnostic profile
   naming keep a later Org migration a re-point, not a redesign. SP-1 does
   **not** build `Org`/`OrgMembership`.
3. **Schema shape — hybrid.** Queryable identity fields are real columns;
   list/nested snapshot data is JSONB.
4. **Versioning — single current profile.** `brand_id` is the PK (one row per
   brand); `PUT` upserts/replaces. `extraction_meta.extracted_at` is retained
   so a future history table is a clean migration, not a redesign.

## Schema — `brand_profile`

One row per brand. PK `brand_id`. No new ENUM (so `downgrade()` is a plain
`drop_table`, sidestepping the enum-drop rule).

```
brand_profile
  brand_id              UUID v7   PK, FK → brand.id  ON DELETE CASCADE
  -- scalar identity (queryable; subsumes the old minimal model) --
  name                  text      NOT NULL
  legal_name            text      NULL
  tagline               text      NULL
  monogram              text      NULL
  brand_color           text      NULL
  founded               text      NULL
  about                 text      NULL
  source_url            text      NULL        -- BrandProfile.url
  industry_vertical     text      NULL        -- free text, NOT an enum
  primary_jurisdiction  varchar(8) NULL       -- ISO-3166 alpha-2
  category_value        text      NULL
  category_confidence   integer   NULL        -- 0..100
  -- JSONB snapshot (evolves with SP-2 without migrations) --
  category_alternatives jsonb     NOT NULL  server_default '[]'::jsonb
  region                jsonb     NOT NULL  server_default '[]'::jsonb
  voice_samples         jsonb     NOT NULL  server_default '[]'::jsonb
  products              jsonb     NOT NULL  server_default '[]'::jsonb
  competitors           jsonb     NOT NULL  server_default '[]'::jsonb
  media_matches         jsonb     NOT NULL  server_default '[]'::jsonb
  extraction_meta       jsonb     NULL      -- {tier,model,cost_usd,
                                            --  js_detected,warnings,extracted_at}
  created_at            timestamptz NOT NULL server_default now()
  updated_at            timestamptz NOT NULL server_default now() onupdate now()
```

`industry_vertical` stays free text because SP-2 emits arbitrary category
strings; an ENUM would add migration friction for no gain. Only `name` (and
`brand_id`) are required; the rest are nullable because onboarding may persist
a partial profile.

## Components

Reuse the existing `service/brand/` DI shape; fix the broken scaffold in
place.

- **`service/brand/model/profile.py`** — rewrite the dead `org_id:int → org.id`
  SQLModel into the table above. JSONB fields use
  `sa_column=Column(JSONB)` with typed `list`/`dict` Python types.
- **`service/brand/repo/profile_repo.py`** — implement the two stubs:
  - `async get(brand_id: UUID) -> BrandProfile | None` — SELECT by PK.
  - `async upsert(profile: BrandProfile) -> BrandProfile` —
    `INSERT … ON CONFLICT (brand_id) DO UPDATE …`, `updated_at = now()`.
  Every query is brand_id-scoped.
- **`service/brand/service.py`** — trim to `get_profile(brand_id)` (raises the
  `core/exceptions.py` not-found error) and `upsert_profile(brand_id, dto)`.
  `structlog` logger built in `__init__`; errors chained with `from e`.
  `contract`/`kb`/`reference_answer` methods stay `NotImplementedError`.
- **`app/api/brand/router.py` + `dto.py`** — see API surface below.
- **`main.py`** — instantiate `BrandContainer`,
  `wire(["cortex_api.app.api.brand.router"])`, mount the brand router.

## API surface

Tenant-scoped, mirroring the working `brand_identity` router pattern.

```
GET  /v1/brand/{brand_id}/profile  -> BrandProfileResponse | 404
     deps: active_brand + requires_brand_capability(VIEW_BRAND_DASHBOARD)

PUT  /v1/brand/{brand_id}/profile  UpsertProfileRequest -> BrandProfileResponse
     deps: active_brand + requires_brand_capability(EDIT_BRAND_SETTINGS)
     semantics: upsert (insert-or-replace the single current profile)
```

The path moves from the scaffold's `/v1/brand/profile` to
`/v1/brand/{brand_id}/profile` for tenant-scoping consistency with
`brand_identity`. `active_brand` already asserts the JWT's
`active_context.kind == "brand"` and that the claim id matches the URL
`brand_id`; the repo re-scopes by `brand_id`. Client `brand_id` is never
trusted beyond the dep.

DTOs are typed — scalars plus nested Pydantic models for the JSON lists, all
optional except `name`. **SP-1 does not import `cortex-brand-extract`.** It
persists whatever DTO is `PUT`; mapping the SP-2 `BrandProfile` to this DTO is
SP-3's `HttpOnboardingApi` projection responsibility (per the program's locked
contract decision).

## Migration

- Add `BrandProfile` to `alembic/env.py` autogenerate imports (profile only;
  contract/kb/reference_answer stay out, deferred).
- One revision after `a1f4c8d2e3b5`. `created_at`/`updated_at` carry
  `server_default=sa.func.now()` (and `updated_at` `onupdate=sa.func.now()`).
  FK `brand_id → brand.id` `ON DELETE CASCADE`. JSONB list columns
  `server_default=sa.text("'[]'::jsonb")`, `nullable=False`.
- No ENUM, so `downgrade()` is a single `op.drop_table("brand_profile")`.
- **Round-trip before push:** `upgrade head` → `downgrade base` →
  `upgrade head`.

## Seed

Extend `scripts/seed_demo_brand.sql` with an idempotent
`INSERT INTO brand_profile (…) … ON CONFLICT (brand_id) DO NOTHING` for the
seeded demo brand, so a fresh environment (docker-compose Postgres on host
`:5433`) has a profile without running the onboarding UI.

## Testing

Cortex convention: override DI container providers, not `mock.patch`.

- **Unit:** model JSONB round-trip (Pydantic ↔ JSONB); repo `get`/`upsert`
  plus upsert idempotency against a transactional Postgres fixture; service
  `get_profile` not-found and `upsert_profile`; DTO ↔ model mapping.
- **API:** endpoint tests with the auth dep and capability gate overridden —
  404 when absent, capability-denied, and upsert-then-get round-trip.
- **Migration:** the `upgrade → downgrade → upgrade` round-trip test.

## Out of scope (deferred)

- `contract` / `kb_source` / `reference_answer` implementation — Placement /
  Agent domains; stay stubbed.
- `Org` / `OrgMembership` convergence — forward-compat invariant only.
- Importing `cortex-brand-extract` or the `BrandProfile` → DTO projection —
  SP-3 (`HttpOnboardingApi`).
- Publisher-side persistence — PHP owns it.
- Versioned/history profiles — forward-compat `extracted_at` only.

## Risks & open questions

- **DTO ↔ model field mapping** must be explicit (snake-case, the JSONB list
  shapes). The implementation plan must enumerate every field; the API accepts
  the persistable subset, not the raw SP-2 type.
- **Capability choice:** read uses `VIEW_BRAND_DASHBOARD`, write uses
  `EDIT_BRAND_SETTINGS` (both exist in `BrandCapability`). If a dedicated
  profile capability is wanted later, it is an additive enum change.
- **Test Postgres:** repo/migration tests need the docker-compose Postgres on
  host `:5433` (the documented local-dev quirk); CI must provide an equivalent.
- **`updated_at` onupdate:** SQLModel keeps `default_factory` for type-check
  ergonomics, but the migration is the SSOT for the server default and
  `onupdate` — both must be set in the migration, per the hard-won rule.

## Key references

- Existing scaffold to fix: `api/src/cortex_api/service/brand/`
  (`model/profile.py`, `repo/profile_repo.py`, `service.py`, `container.py`)
- Auth spine: `api/src/cortex_api/app/dependencies/{auth,brand,capability}.py`,
  `service/brand_identity/model/brand_tenant_ctx.py`
- Migration precedent + rules: `api/alembic/versions/8e4ef4f9b295_*`,
  `a1f4c8d2e3b5_*`, and the hard-won Alembic rules in `CLAUDE.md`
- Seed precedent: `api/scripts/seed_demo_brand.sql`
- SP-2 shape: `packages/brand-extract/src/cortex_brand_extract/types.py`
- Program contract decision: SP-2 spec
  `docs/superpowers/specs/2026-05-18-brand-extraction-engine-design.md`
