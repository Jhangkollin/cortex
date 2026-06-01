# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@../aigc_coordinator/CLAUDE.md

## Repo at a glance

Green-field insights dashboard product (Brand + Publisher views) deployed on AWS EKS in Tokyo (`ap-northeast-1`), sibling to agent-will-smith. It will eventually replace aigc-mvp's role as the primary tenant-facing product.

Cortex is live on UAT since 2026-05-12 (data-platform-helm-charts PR #49 + data-platform-iac PR #25). Bumps go through `feat/cortex-uat-promote-<sha>` branches → PR → merge → `make helm-cortex ENV=uat`. See "UAT bring-up landmines" below for the gotchas that surfaced during go-live.

- **api/** — FastAPI service (`cortex-api`). Mirrors agent-will-smith's three-tier DI layout (`core` → `infra` → `service`).
- **web/** — Next.js 16 (App Router) + Tailwind + shadcn/ui. NextAuth + Google OAuth.
- **deploy lives elsewhere** — Helm + Terraform are in `../infra/data-platform-helm-charts/` and `../infra/data-platform-iac/`. This repo only builds and pushes to ECR.

## Conventions to mirror from agent-will-smith

- Three-tier DI: `CoreContainer → InfraContainer → ServiceContainer` (wired in `main.py` only)
- Exceptions only from `core/exceptions.py`, always chain with `from e`
- Logger: `structlog.get_logger(__name__)` in `__init__`, never module-level
- Config: Pydantic `BaseSettings` with `env_prefix`. Two-tier prefix scheme:
   - **Core configs** use `CORE_*` (e.g. `CORE_DB_*`, `CORE_AUTH_*`, `CORE_REDIS_*`, `CORE_DATABRICKS_*`, `CORE_FASTAPI_*`, `CORE_LOG_*`, `CORE_VECTOR_SEARCH_*`). The same `CORE_DB_*` contract is what `alembic/env.py` resolves through `DatabaseConfig`, and what the helm chart provides via env vars.
   - **Service configs** use `CORTEX_<DOMAIN>_*` (e.g. `CORTEX_IDENTITY_*`, `CORTEX_BRAND_IDENTITY_*`, `CORTEX_PUBLISHER_IDENTITY_*`, `CORTEX_BRAND_DASHBOARD_*`). One prefix per service domain.
- Middleware: pure ASGI only (no `BaseHTTPMiddleware`). Cortex now keeps **only** observability + CORS as middleware — auth and tenant resolution are FastAPI `Depends` (see below)
- Testing: override DI container providers, not `mock.patch`
- Pydantic v2 for all DTOs / config; SQLModel + Alembic for persistence
- Databricks SQL connector is sync — wrap calls in `loop.run_in_executor`

## Domain boundaries (DDD)

Okis' domain model is the target language. It separates shared vocabulary,
actor/foundation contexts, capability contexts, versioned library assets, and
the Insights read model:

- **Shared kernel** — read-only VOs any context may use: `OrgId`, `UserId`,
  `PersonaType` (`BRAND` / `PUBLISHER` / `DEVELOPER`), `Money`,
  `Jurisdiction`. It has no internal dependencies.
- **Identity foundation** — target model is `Org`, `AppUser`,
  `OrgMembership`. It owns who the user is and which org/persona they may act
  as. Every aggregate in every context scopes to an `OrgId`.
- **Actors** — `Brand` and `Publisher` are actor contexts. Brand owns profile,
  contracts, KB sources, reference answers, products, and onboarding.
  Publisher owns profile, contracts, and a pointer to versioned publisher
  persona assets.
- **Capabilities** — `Discovery`, `Placement`, and `Agent` own work. Discovery
  ingests articles/questions/topics/intent. Placement decides eligible Brand
  answers and snapshots decision factors. Agent composes prompts, reads Library
  assets, calls LLMs, and runs quality gates.
- **Library** — versioned, read-only assets consumed by Agent and Placement:
  vertical rules, publisher personas, disclosures, prompt templates, and intent
  taxonomy.
- **Insights** — persona-agnostic Databricks read model (`Metric`, `Funnel`,
  `Cohort`, `Digest`, `Prediction`, `Recommendation`) consumed by dashboard
  APIs. Persona-flavored shaping belongs at the app/API boundary.

Current MVP code still has compatibility scaffolds named `brand_identity` and
`publisher_identity` because Brand login/onboarding shipped first and Publisher
tables are not migrated yet. Do not extend that split into new business
domains. Future identity work should converge toward the shared
`Org`/`OrgMembership` foundation instead of adding more per-persona identity
tables by default.

Insights is **not** split into per-persona bounded contexts. The
route modules `app/api/brand_dashboard/` and `app/api/publisher_dashboard/`
are API projections over the shared Insights read model. Persona-specific
choices such as metric catalogs, default breakdowns, capability names, and DTO
wording live at those projection edges. Shared calculation, cache-key, funnel,
and Databricks row-mapping behavior belongs in `service/insights/` once a
second projection needs the same shape. Do not copy the Brand Dashboard
projection to implement a Publisher surface.

### Scoping keys

- `brand_id` (UUID v7) — universal scoping key on brand side. **Same value as PHP's `brand_uuid`** (see aigc-mvp coordinator notes); the two systems share brand identity so a brand created in one is addressable from the other.
- `publisher_id` (UUID v7) — universal scoping key on publisher side. Cortex-only; PHP currently owns publisher onboarding.
- UUID v7 generator: `cortex_api.core.identifiers.uuid7()` (time-ordered, RFC 9562 §5.7).

Every Databricks query and every vector search **must** filter by the active context's id. Never trust client-supplied scoping — derived from JWT only.

## Capability passing (the auth core)

Authorization is **zero-DB on the hot path**. Capabilities are computed at login by `BrandCapabilityPolicy` / `PublisherCapabilityPolicy`, baked into the JWT, and verified per request via FastAPI `Depends` — no Redis lookup, no Postgres lookup.

### JWT shape

NextAuth signs the JWT after Google OAuth. Cortex-API verifies signature + decodes claims via `app/dependencies/auth.py`. Beyond standard claims (`sub`, `email`, `iss`, `aud`, `exp`), Cortex adds:

```json
{
  "active_context": {
    "kind": "brand",
    "id": "<uuid v7>",
    "role": "admin",
    "capabilities": [
      "view_brand_dashboard",
      "edit_brand_settings"
    ]
  }
}
```

Switching context (different brand, or brand→publisher) requires resolving membership via `POST /v1/auth/resolve-context` and re-issuing the JWT from NextAuth. There is intentionally no "current org" mutable on the server — the client always presents a JWT and the JWT decides scope.

### FastAPI Depends pattern (replaces middleware)

| Dep | What it returns | What it asserts |
|---|---|---|
| `authenticated_user` | `AuthedUser` VO | bearer token valid, signature OK |
| `active_brand` | `BrandTenantCtx` VO | JWT's `active_context.kind == "brand"`, claim id matches URL `brand_id` |
| `active_publisher` | `PublisherTenantCtx` VO | JWT's `active_context.kind == "publisher"`, claim id matches URL `publisher_id` |
| `requires_brand_capability(cap)` | None | the BrandTenantCtx contains `cap` in its capabilities tuple |
| `requires_publisher_capability(cap)` | None | mirror for publisher |

A route signature spells out its requirements:

```python
@router.get("/v1/brand/{brand_id}/analytics/metrics")
async def get_metrics(
    tenant: BrandTenantCtx = Depends(active_brand),
    _: None = Depends(requires_brand_capability(BrandCapability.VIEW_BRAND_DASHBOARD)),
) -> MetricsDTO:
    ...
```

If you're tempted to write a middleware that sets `request.state.<something>` — don't. Use a Depends.

### `current_app_user`: bootstrap vs session JWT dispatch

`current_app_user` (in `app/dependencies/auth.py`) dispatches on the `token_kind` claim that cortex-web's NextAuth signers stamp:

- `"bootstrap"` — JWT carries Google `oauth_subject`; `UserService.recognize_user` upserts the AppUser row (first-ever sign-in creates it, subsequent bootstrap calls refresh display name / avatar). This is the onboarding flow.
- `"session"` — JWT `sub` already IS the AppUser UUID (resolved on a prior bootstrap). The dep just fetches by id. Normal request handling.
- missing / unknown `token_kind` — 401. Surfaces NextAuth misconfiguration (e.g. legacy session cookies minted before this contract was tightened) at the boundary rather than silently routing into the wrong branch.

If you add a new token shape, extend the dispatch here and update `docs/auth.md` § "Bootstrap vs session token shapes" — do not add token-kind logic inside services.

## CQRS: write side vs read side

OLTP write-side contexts and the Insights read model use different patterns:

| Side | What | Pattern | Storage |
|---|---|---|---|
| **Write** | current `app_user`, `brand`, `brand_membership`; target `org`, `app_user`, `org_membership` plus actor-owned tables | Active Record via SQLModel | Postgres (RDS) |
| **Read** | Insights shared primitives + dashboard/API projections, knowledge_base | Frozen Pydantic value objects (NOT SQLModel) | Databricks gold tables + Vector Search |

The dividing rule: SQLModel only for things Cortex itself writes back to its
OLTP. Insights rows come from Databricks and are projected straight into
immutable Pydantic VOs — never SQLModel, never ORM. Conflating the two
patterns is a code-review red flag.

## Persistence

OLTP is **AWS RDS Postgres** in `ap-northeast-1` (Lakebase isn't released in this region yet — see `docs/architecture.md`). Drivers/SQLModel/Alembic are Postgres-generic, so a future Lakebase migration is a DSN change.

### Migrations

Alembic + async (`asyncpg` online, `psycopg` offline). `alembic/env.py` imports SQLModel tables for autogenerate detection.

**MVP schema** (initial migration `8e4ef4f9b295_initial_brand_identity_app_user_brand_.py` on `feature/initial-migration`, PR #4):

- `app_user` (UUID v7 PK, `oauth_subject` UNIQUE, `email`, `display_name`, `avatar_url`, timestamps)
- `brand` (UUID v7 PK, `display_name`, `industry`, `domain`, `archived_at`, timestamps)
- `brand_membership` (UUID v7 PK, FK→`app_user.id`, FK→`brand.id`, `role` brandrole enum, `invited_by` FK→`app_user.id`, UNIQUE(user_id, brand_id))
- Postgres ENUM `brandrole` (`viewer` | `editor` | `admin`)

**Founder uniqueness — DROPPED 2026-05-26** (`7ab199ba95a2_drop_brand_membership_founder_unique_.py`). Originally (`a1f4c8d2e3b5`, 2026-05-12) a Postgres partial `UNIQUE` index on `brand_membership(user_id) WHERE invited_by IS NULL` enforced "one founder membership per user" and closed a TOCTOU race in `create_brand_with_admin`. The **multi-brand onboarding** decision (each onboarding creates a new, independent brand; no override) removed it: `create_brand_with_admin` now always creates a new brand + ADMIN founder membership. **Accepted tradeoff:** the DB no longer fail-fasts a duplicate founder INSERT, so the live first-sign-in path (persona picker → `POST /v1/brand`) can create duplicate brands on a double-click / retry / concurrent tabs — to be mitigated at the UI layer (disable-on-submit) when the multi-brand entry point ships. `UniqueConstraint(user_id, brand_id)` still prevents a duplicate membership in the *same* brand. (Migration `downgrade()` recreates the index and will fail if any user already holds 2+ founder rows — a known one-way-door once multi-brand data exists.)

**Publisher tables are intentionally NOT migrated at MVP** — PHP retains ownership of the publisher side. When the publisher slice begins, add the publisher SQLModel imports back into `alembic/env.py` and generate a follow-up migration. No `publisher` / `publisher_membership` / `publisherrole` exist yet.

### Migrations: hard-won rules

These are not optional — autogen will skip them, and the absence will bite you.

1. **`server_default=sa.func.now()` on every `created_at`; `server_default` + `onupdate=sa.func.now()` on every `updated_at`.** The database is the SSOT for row timestamps. SQLModel's `default_factory=datetime.utcnow` is kept for type-checker / unit-test ergonomics, but raw SQL inserts (seed scripts, `psql` fixups, batch imports) bypass it and a `NOT NULL` column with no server default fails. Equivalently, `updated_at` without `onupdate` is frozen at insert time — silently turning into a second `created_at` after the first save.
2. **Drop Postgres ENUMs explicitly in `downgrade()`.** `op.drop_table()` does not drop the named ENUM type. Re-upgrade after downgrade fails with `type "<name>" already exists`. Append `sa.Enum(name='<name>').drop(op.get_bind(), checkfirst=True)` after the `drop_table` lines in `downgrade()`.
3. **Round-trip test before pushing.** `alembic upgrade head` → `downgrade base` → `upgrade head`. The middle downgrade is the one that catches missed enum drops.

### Seed scripts

`api/scripts/seed_demo_brand.sql` is the canonical bootstrap for a fresh environment: idempotent INSERTs for first brand + owner user + ADMIN membership. Pass `brand_id`, `owner_email`, `owner_oauth_subject` as psql `-v` variables. Ops generates the `brand_id` UUID v7 ahead of time — the same value is later baked into JWT claims at login and used as `brand_uuid` in Databricks `WHERE` clauses.

## Local dev quirks

- **`docker-compose up` brings up postgres + redis.** Postgres is exposed at host port `5433:5432` (not `5432:5432`). This avoids the very common conflict with a Homebrew postgres bound to host `127.0.0.1:5432` — without this you get "role cortex does not exist" because asyncpg connects to Homebrew instead of the container. `alembic.ini` uses `localhost:5433` to match. Redis is exposed at `6379:6379` and is required by the api container. If you have no host postgres and want plain `:5432`, override locally via `docker-compose.override.yml`.
- **`greenlet>=3.0.0` is a hard dep.** SQLAlchemy async + Alembic autogenerate need it; uv pulls it transitively now, but if you ever see `MissingGreenlet`, this is why.

## UAT bring-up landmines

Captured during the 2026-05-12 go-live. Re-read before touching the Dockerfile, configs, or auth shape:

- **Dockerfile must include `readme = ...` in `pyproject.toml` and set the correct `WORKDIR` for `uv` builds.** Missing readme breaks `uv build`; wrong WORKDIR breaks module discovery in the runtime image.
- **Buildx arm64 emulation is required for local image builds on Apple Silicon.** The ECR target is `linux/amd64`; without `docker buildx build --platform linux/amd64 ...` you ship the wrong architecture.
- **Configs use `env_prefix = "CORE_"` (or `CORTEX_<DOMAIN>_`).** `.env` keys must follow the prefix — naming a key `DATABASE_URL` instead of `CORE_DB_HOST`/`CORE_DB_PASSWORD`/... silently falls back to defaults.
- **configparser chokes on `%` in DSN values.** Passwords containing `%` must be escaped as `%%` anywhere they pass through configparser (e.g. `alembic.ini`). `alembic/env.py` bypasses configparser and reads the DSN via `DatabaseConfig` precisely to dodge this trap.
- **NextAuth defaults to JWE; cortex-web overrides to JWS so PyJWT can verify.** If a token starts with `eyJlbmM...` (JWE) instead of `eyJhbGc...` (JWS), the override regressed and the api returns 401 across the board.
- **`alembic/env.py` bypasses configparser to load the DSN** through `DatabaseConfig`. Necessary because of the `%` trap above — do not "simplify" this back into `alembic.ini`.
- **Migrations were run via `kubectl cp` until OPT22 added a CI/CD migration step.** Older runbooks may still reference the manual flow; the automated step is the canonical path now.

## Domain layout (canonical surfaces)

```
api/src/cortex_api/service/
  identity/              ← current AppUser; target Identity foundation owns Org/AppUser/OrgMembership
  brand_identity/        ← current Brand-side compatibility scaffold (container/service/config/policy/repo/model)
  publisher_identity/    ← current Publisher-side compatibility scaffold (container/service/config/policy/repo/model); tables not migrated
  insights/              ← persona-neutral Databricks read-model primitives / interfaces
  brand_dashboard/       ← current Brand Dashboard API adapter over Insights (with config)
  publisher_dashboard/   ← placeholder adapter; reuse insights/, do not copy Brand Dashboard
  knowledge_base/        ← placeholder; future Library assets should be versioned
  connectors/            ← placeholder, GA4 / CRM / publisher feeds
  admin/                 ← placeholder service slot (README + __init__ only); the live admin surface
                          today is `app/api/admin/` (router + dto), future PHP replacement
```

Most write-side domains are a pair: `app/api/<name>/` (router + DTO) +
`service/<name>/` (container, service, config, repo, model[, policy]). Insights
is different: `service/insights/` holds persona-neutral read-side
primitives/interfaces, while dashboard route modules shape those primitives for
Brand or Publisher. The shape of `service/brand_identity/` is **not** the
template for new capability contexts such as Discovery, Placement, Agent, or
Library.

## Testing

Tests are part of the change — feature PRs land with the matching test in the same PR.

**api/ (pytest):**
- Default test target = unit tests, no DB required.
- Integration tests are tagged with the `integration` marker (declared in `api/pyproject.toml`) and require docker-compose Postgres up.
- Local fast loop: `pytest -m "not integration"` skips the DB-bound suite.
- Full run including integration: `pytest` (after `docker-compose up -d`).
- DI overrides: tests override container providers, never `mock.patch`.

**web/ (vitest + jsdom):**
- Harness lives at `web/vitest.config.ts` (jsdom env, `@/*` path alias, jest-dom matchers, localStorage cleared between tests). Introduced in PR #18.
- Tests are picked up from both co-located `src/**/__tests__/*.test.tsx` and cross-cutting `web/tests/**/*.test.tsx`.
- NextAuth session mocking helpers: `web/tests/helpers/render-with-session.tsx` and `session-mock-state.ts`.
- `npm test` runs vitest once; `npm run test:watch` is the dev loop.

## Common commands

Top-level Makefile fans out to `api/` and `web/`:

```bash
make test                       # api + web test suites
make lint                       # ruff + mypy (api), eslint + tsc (web)
make generate-client            # regen web/src/lib/api-client/generated/ from cortex-api OpenAPI

# api/ — Python (uv, Python 3.12)
cd api
uv sync --all-extras
docker-compose up -d            # local postgres (host port 5433) + redis
cp .env.example .env            # fill in secrets (Databricks, JWT)
uv run alembic upgrade head     # apply migrations
uv run uvicorn cortex_api.main:app --reload --port 8000   # → http://localhost:8000/docs

make test                       # pytest with coverage
make lint                       # ruff check + ruff format --check + mypy
make format                     # apply ruff format + autofix
make migrate                    # alembic upgrade head
make migration-new NAME="add foo"
uv run pytest tests/unit/test_app_boots.py -v
uv run pytest -k "membership"

# web/ — Next.js 16
cd web
npm install
npm run dev                     # Turbopack dev server → http://localhost:3000
npm run build                   # production build (standalone output)
npm run lint                    # eslint
npm run type-check              # tsc --noEmit
npm test                        # vitest run
npm run test:watch              # vitest watch
```

## Architecture quick map

```
app/      ← FastAPI surface
  ├── api/<domain>/{router.py, dto.py}
  ├── dependencies/{auth, brand, publisher, capability}.py  ← authz spine (no auth middleware)
  └── middleware/observability_middleware.py                ← only middleware remaining
service/  ← business logic, one container per domain
  └── <domain>/{container.py, service.py, config.py, repo/, model/, policy/}
infra/    ← clients (postgres, redis, databricks SQL, vector search) + InfraContainer
core/     ← Pydantic configs, structlog setup, exceptions, CoreContainer, identifiers (uuid7)
main.py   ← only place that wires containers and mounts routers
```

`main.py` adds two middleware (observability + CORS) and wires all containers. Everything else flows through Depends.

## Deploy

See `docs/deploy.md`. Cortex CI builds + pushes to ECR. Helm release is a follow-up PR in `../infra/`.

## Key references

- `../aigc_coordinator/cortex-scaffolding-design.md` — original scaffolding design (predates the brand/publisher refactor; some sections superseded)
- `../aigc_coordinator/cortex-mvp-plan.md` — MVP delivery plan with feature slices
- `../aigc_coordinator/cortex-tech-stack.md` — broader architectural reference
- `../agent-will-smith/CLAUDE.md` — convention source
- `../infra/CLAUDE.md` — deploy + Pod Identity rules
- [Backend architecture wiki](https://github.com/mlytics/cortex/wiki/Backend-architecture) — DDD + clean-architecture notes. Out-of-repo, not versioned with the code; treat as supplementary, not canon.
