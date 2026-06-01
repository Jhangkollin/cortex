# SP-3a — Product-mode HttpOnboardingApi + Analyze Pipeline — Design

- **Date:** 2026-05-18
- **Status:** Approved (brainstorming) — ready for implementation planning
- **Scope:** SP-3a of the Brand Onboarding program. Covers **only** product-mode
  (authenticated, tenant-scoped) real `analyzeBrand`: the async analyze
  endpoint + job model, the cortex-api SP-2→SP-1 worker, and the web
  `HttpOnboardingApi` adapter with its `BrandProfile → ExtractedBrand`
  projection. The GTM public/pre-auth surface is **SP-3b** (next); SP-4
  depends on SP-3b.

## Context

SP-3a makes the onboarding wizard's `analyzeBrand` genuinely real behind the
seam shipped in #29. A real brand URL flows: server-side SP-2 extraction →
SP-1 persistence → projected `ExtractedBrand` rendered by the **unchanged**
wizard. The other six `OnboardingApi` methods stay modeled inside the adapter
(no backend yet — a conscious, documented hybrid).

| Spike | Status |
|---|---|
| SP-1 — brand profile write model + persistence | done (merged #31 `7cb0d01`) |
| SP-2 — extraction engine `cortex-brand-extract` | done (merged #28 `fade966`) |
| SP-3 FE contract-seam (`OnboardingApi` / `getOnboardingApi()`) | done (merged #29 `3077f90`) |
| **SP-3a** — product-mode real `analyzeBrand` (this spec) | designing |
| SP-3b — GTM public/pre-auth surface | not started |
| SP-4 — Brand Insight one-pager | not started (depends on SP-3b) |

### Grounded reality (verified on develop@`3077f90`)

- **#29 seam is real:** `web/src/lib/onboarding/api.ts` exposes the
  `OnboardingApi` interface + `getOnboardingApi()` factory + a `SEAM` marker
  and a `BrandProfile → ExtractedBrand` projection contract note;
  `MockOnboardingApi` and a mock-parity test exist. The wizard already renders
  via the seam and has explicit loading + error/retry UX and a shared
  `loadAll(url)` (mount and restart) with an `INITIAL_URL` constant.
- **#31 SP-1 is real:** `brand_profile` table (PK `brand_id` → `brand.id`),
  atomic `INSERT … ON CONFLICT (brand_id) DO UPDATE` upsert, model-derived
  replace set, `GET`/`PUT /v1/brand/{brand_id}/profile` behind `active_brand`
  + capability gates. The single current profile is replace-on-write.
- **#28 SP-2 is real:** `packages/brand-extract/` ships `cortex_brand_extract`
  with `extract_brand_profile(...)` producing a frozen `BrandProfile`
  (snake_case, nullable fields, no UI fields). Pluggable BYO-key LLM
  (Claude default + OpenAI-compat). Tiered fetch. Sync API. Degrade paths emit
  structured warnings. Extraction is **slow and costly** (seconds + dollars
  per brand).
- **Auth spine is zero-DB:** JWT → `AuthedUser` → `BrandTenantCtx`, with
  `active_brand` and `requires_brand_capability` FastAPI deps. Cross-tenant
  claim/URL mismatch raises `ContextMismatchError` → **HTTP 400** (verified in
  `app/exception_handlers.py`); `Forbidden/Membership` → 403.

## Locked decisions

1. **Async job + poll.** `analyzeBrand` → `POST …/profile/analyze` returns
   **202 + job_id**; the wizard polls a status endpoint until terminal. SP-2
   extraction far exceeds a safe synchronous HTTP window (ALB/ingress idle
   timeouts), and a retry must not replay LLM cost. The #29 loading /
   crawl-animation / error+retry UX is the progress surface.
2. **Postgres job table + in-process async worker.** Job state lives in a new
   `brand_profile_analysis_job` row in the same RDS Postgres as the SP-1
   write-side, so any EKS api replica can serve a poll. The analyze request
   spawns an in-process `asyncio` task; no new infra (no Redis worker
   deployment) at MVP.
3. **Server-managed LLM key.** Product mode uses a server-side key from
   cortex-api config / Secrets (existing `CoreContainer` `BaseSettings` +
   `env_prefix` pattern), **not** a tenant key. Per-job `cost_usd` is recorded.
4. **Re-analyze dedupes to the in-flight job.** A second `analyze` for a brand
   with a job already `pending`/`running` returns that job_id rather than
   spawning a duplicate (costly) extraction. Re-analyze after a terminal job
   starts a fresh job; SP-1's upsert replaces the single current profile. The
   server is the single source of truth — this **absorbs the deferred #29
   `loadAll` re-entrancy follow-up**; no client-side AbortController is added.
5. **Projection lives in `HttpOnboardingApi`.** SP-1 and SP-2 stay UI-agnostic
   (program's locked contract). The adapter owns `BrandProfile`(snake,
   nullable) → `ExtractedBrand`(camel; synthesized `id`/`picked`/`icon`;
   derived `productMoreCount`).
6. **Hybrid adapter.** Only `analyzeBrand` is real. `getCrawlTasks`,
   `getMediaNetwork`, `getLiveQuestions`, `getVoiceTones`, `getDeployAgents`,
   `getDeployLog` return the same modeled data the mock used — explicitly,
   with a documented TODO referencing SP-3b / later slices.

## Schema — `brand_profile_analysis_job`

One row per analyze attempt (history retained; not keyed by brand).

```
brand_profile_analysis_job
  id            UUID v7     PK  (cortex_api.core.identifiers.uuid7)
  brand_id      UUID        NOT NULL  FK → brand.id  ON DELETE CASCADE
  status        analyzejobstatus  NOT NULL   -- Postgres ENUM, default 'pending'
  source_url    text        NOT NULL
  cost_usd      numeric(10,4) NULL    -- filled on success from extraction_meta.cost_usd
  error         text        NULL      -- failure summary (no secrets / no stack)
  created_at    timestamptz NOT NULL  server_default now()
  updated_at    timestamptz NOT NULL  server_default now()  onupdate now()
  INDEX ix_brand_profile_analysis_job_brand_id_status (brand_id, status)
```

`status` is a Postgres ENUM `analyzejobstatus` driven by a Python
`AnalyzeJobStatus(StrEnum)` (`pending|running|succeeded|failed`) — this
**mirrors the codebase's only status-column precedent (`brandrole`)**; there
is no CHECK-constraint pattern in this repo, so following the established
ENUM convention is correct. Per the hard-won Alembic rule, `downgrade()` does
`op.drop_table(...)` **then**
`sa.Enum(name="analyzejobstatus").drop(op.get_bind(), checkfirst=True)` (the
table drop does not drop the named ENUM). Timestamps carry
`server_default=sa.func.now()` and `updated_at` `onupdate=sa.func.now()` per
the hard-won rule. The migration's `down_revision = "c3d4e5f6a7b8"` (the
current head, #31's `brand_profile`); the SQLModel is added to
`alembic/env.py` autogenerate imports. Round-trip
(`upgrade → downgrade → upgrade`) before push.

## API surface

Tenant-scoped, mirroring the working `brand` profile router.

```
POST /v1/brand/{brand_id}/profile/analyze   AnalyzeRequest{ url }  -> 202 AnalyzeJobDTO
     deps: active_brand + requires_brand_capability(EDIT_BRAND_SETTINGS)
     semantics: dedupe to in-flight job for brand_id; else insert job
                (status=pending) + spawn worker; return {job_id,status}

GET  /v1/brand/{brand_id}/profile/analyze/{job_id} -> AnalyzeJobDTO
     deps: active_brand + requires_brand_capability(VIEW_BRAND_DASHBOARD)
     asserts: job.brand_id == tenant brand_id (else NotFound — never leak
              another tenant's job; consistent with the 400/404 contract,
              never 200 with foreign data)
     body: { job_id, status, error?, cost_usd?, profile? }
           profile present only when status == 'succeeded'
           (the persisted BrandProfile as the SP-1 GET shape)
```

`AnalyzeJobDTO` is typed (Pydantic v2). The endpoint persists/returns the
SP-1 profile shape; the **web adapter** performs the `BrandProfile →
ExtractedBrand` projection (locked decision 5). cortex-api never trusts a
client `brand_id` beyond the dep; the worker writes the JWT-scoped `brand_id`.

## Components

- **Migration:** one revision after #31's head adding
  `brand_profile_analysis_job`; add the SQLModel to `alembic/env.py`.
- **`service/brand/model/analysis_job.py`** — SQLModel for the table
  (uuid7 default, typed status, timestamps with server defaults/onupdate).
- **`service/brand/repo/analysis_job_repo.py`** — stateless, session-per-call
  via `DatabaseClient.session()`: `create`, `get(brand_id, job_id)`,
  `find_in_flight(brand_id)`, `mark_running/succeeded/failed`,
  `sweep_stale(ttl)`. Every query is `brand_id`-scoped.
- **`service/brand/analyze_service.py` — `AnalyzeJobService`** (a dedicated
  unit, separate from profile CRUD `service.py`; single responsibility =
  analyze jobs) — logger built in `__init__`
  (`structlog.get_logger(__name__)`); exceptions from `core/exceptions.py`,
  chained `from e`. `start_analyze(brand_id, url)`:
  dedupe → create job → schedule the worker coroutine. `get_job(brand_id,
  job_id)`. The worker coroutine **`await`s SP-2's
  `extract_brand_profile(url, provider=<built>, tier="lite")` directly — it
  is `async`, not sync** (no `run_in_executor`); the provider is built from
  config as `ProviderConfig(kind, api_key, model, base_url)` →
  `ClaudeProvider(cfg)` / `OpenAICompatProvider(cfg)`. It then maps SP-2's
  `cortex_brand_extract.BrandProfile` → SP-1's `BrandProfile` SQLModel,
  calls the **existing SP-1 upsert path**, then `mark_succeeded` (+
  `cost_usd` from `result.extraction_meta.cost_usd`) or `mark_failed`
  (sanitized message). Caught `cortex_brand_extract.errors.{UpstreamError,
  UpstreamTimeoutError,ExtractError}` re-raise as the cortex-api
  `core.exceptions` equivalents **chained `from e`** (→ 502/504). A
  startup/lazy `sweep_stale` flips
  `running` jobs older than a TTL to `failed` so a pod restart yields a
  retryable job, never a stuck poll.
- **`service/brand/analyze_config.py` — `AnalyzeConfig(BaseSettings)`**
  (`env_prefix="CORTEX_ANALYZE_"`, `extra="forbid"`, mirrors SP-1 `config.py`):
  `provider_kind: Literal["claude","openai_compat"]`, `api_key: str`,
  `model: str`, `base_url: str | None`, `tier: str = "lite"`,
  `stale_job_seconds: int`. Server-managed key — config/Secrets only, never
  logged, never in DTO/error.
- **`app/api/brand/router.py` + `dto.py` (extend)** — the two routes above
  added to the **existing** brand router/dto (no new `app/api/<name>/` dir),
  with `AnalyzeRequest` / `AnalyzeJobDTO`.
- **cortex-api dependency (net-new wiring)** — add `cortex-brand-extract` to
  `api/pyproject.toml` `[project] dependencies` **and** a
  `[tool.uv.sources] cortex-brand-extract = { path = "../packages/brand-extract", editable = true }`
  entry (no prior precedent in this repo); `uv sync` after. Lite tier needs
  no `[render]` extra. Import only at the worker boundary.
- **DI wiring** — register `analyze_config`, `analysis_job_repo`,
  `AnalyzeJobService` providers in the **existing `BrandContainer`**
  (`providers.Singleton`, deps named as kwargs — SP-1 pattern). **`main.py`
  needs zero edits**: the analyze routes live in the already-included
  `brand_router`, and `BrandContainer` is already instantiated, in
  `_all_containers()`, and `.wire(modules=["cortex_api.app.api.brand.router"])`.
  The worker task is `asyncio.create_task(...)`; the service holds a strong
  reference in a `set[asyncio.Task]` with a `task.add_done_callback(set.discard)`,
  and a FastAPI lifespan/shutdown hook cancels any still-running tasks.
- **web `HttpOnboardingApi`** — implements the `OnboardingApi` port behind
  `getOnboardingApi()` (swap the literal `// SEAM:` line in
  `web/src/lib/onboarding/api.ts`; no env flag exists). **Boundary
  constraint:** the wizard is `"use client"`, and cortex-api token signing is
  **server-only** (`web/src/lib/cortex-api.ts` + `cortex-token.ts`,
  `import "server-only"`). So:
  - A **server-only function** in/alongside `cortex-api.ts`,
    `analyzeBrandProfileStart/Poll(claims, brandId, …)`, mints the ephemeral
    bearer (`signCortexApiToken`) and `fetch`es the two cortex-api routes
    (`cache: "no-store"`, `throw` on `!res.ok`) — mirroring the existing
    `updateBrand` convention; cortex-api DTOs mirrored as TS interfaces.
  - A **Next.js Server Action** wraps those (gets `brandId` from
    `session.user.activeContext.id`).
  - `HttpOnboardingApi` (client class) `analyzeBrand(url)` calls the Server
    Action, runs the bounded poll loop (`pending|running` → continue;
    `failed` → throw so the #29 `catch` shows error+retry; `succeeded` →
    project), and **owns the `BrandProfile → ExtractedBrand` projection**:
    snake→camel, null-coalesce nullable strings to `""`, `url→`url`/source,
    synthesize per-item `id`/`icon`/`picked`, map `match_score→matchScore`,
    derive `productMoreCount = max(0, products.length - VISIBLE_N)`.
  - The other six methods delegate to the existing modeled data with an
    explicit `// SP-3b / later` TODO. The mock-parity test stays green; a new
    `HttpOnboardingApi` projection test mocks the boundary and deep-equals an
    expected `ExtractedBrand`.

## Data flow

```
wizard (web, #29 seam)
 → HttpOnboardingApi.analyzeBrand(url)
   → POST /v1/brand/{brand_id}/profile/analyze            → 202 {job_id,status}
      → AnalyzeJobService.start_analyze: dedupe → job(pending) → create_task
         worker: await extract_brand_profile(url, provider, tier="lite")  [async]
               → map SP-2 BrandProfile → SP-1 BrandProfile → SP-1 upsert
               → job(succeeded, cost_usd) | job(failed, error)
   → (Server Action) poll GET …/analyze/{job_id} until terminal  (#29 anim = progress)
   → succeeded: profile in body → HttpOnboardingApi projects → ExtractedBrand
 → wizard renders (UI unchanged; #29 error+retry on job=failed)
```

## Testing

Cortex convention: override DI container providers, not `mock.patch`.

- **api unit/integration:** job repo (`create`/`get`/`find_in_flight`/
  `mark_*`/`sweep_stale`) against the transactional Postgres fixture
  (docker-compose host `:5433`); `AnalyzeJobService` with SP-2 mocked at the
  library edge (fast, deterministic) — success path persists via SP-1 and
  marks `succeeded` with `cost_usd`; failure path marks `failed` with a
  sanitized message; dedupe returns the in-flight job_id; stale sweep flips
  an aged `running` job.
- **api endpoint:** auth dep + capability gate overridden — `POST` returns
  202 + job_id; `GET` reflects the lifecycle; **cross-tenant `GET` is
  rejected** (job of brand A not visible to brand B; never 200 with foreign
  data — mirrors #31's contract); capability-denied paths.
- **web:** projection unit tests (snake→camel, null-coalesce, synthesized
  `id`/`picked`/`icon`, `productMoreCount`); the poll state machine
  (`pending→running→succeeded`, and `→failed→` retry) using the #29 seam
  fakes; the mock-parity test stays green; `getOnboardingApi()` returns the
  Http adapter under the production flag/condition.
- **migration:** `upgrade → downgrade → upgrade` round-trip.

## Out of scope (deferred)

- **SP-3b** — GTM public/pre-auth surface (unauthenticated analyze, no
  tenant). SP-4 (Brand Insight one-pager) depends on SP-3b.
- Real backends for the other six `OnboardingApi` methods.
- Redis/dedicated-worker job infra (Postgres + in-process worker at MVP).
- A job *history* UI / multiple retained profiles (rows are retained;
  surfacing them is later).
- Already-tracked PR-comment follow-ups: #28 Issue 1 (LLM-contract
  single-source-of-truth, incl. openai_compat `strict:true`), #31 Issue 3
  (DTO request/response symmetry).

## Risks & open questions

- **Worker durability:** an in-process task dies with the pod. Mitigated by
  the stale-`running` sweep (→ `failed`, retryable) and cheap re-analyze
  (poll/dedupe, no duplicate extraction). If durability becomes a
  requirement, Redis/arq + a worker Deployment is the documented next step
  (locked decision 2 keeps this a swap, not a redesign).
- **Task lifecycle:** the spawned `asyncio` task must be strongly referenced
  (not GC'd) and cancelled on app shutdown; the implementation plan must make
  this explicit.
- **Cost/abuse:** dedupe-to-in-flight bounds concurrent cost per brand; a
  per-brand rate/budget guard is **not** in SP-3a (note for SP-3b where the
  surface is unauthenticated and abuse risk is higher).
- **SP-2 secret handling:** the server key is config/Secrets only; never
  logged, never returned in `AnalyzeJobDTO`, never in `error`.
- **Poll cadence:** client interval/backoff and a hard client-side timeout
  must bound a stuck poll even with the server sweep; the plan must specify
  values and the failed-after-timeout UX (reuses #29 error+retry).

## Key references

- #29 seam: `web/src/lib/onboarding/{api.ts,mock-api.ts}`,
  `web/src/app/(auth)/onboarding/v2/*` (loading/error/retry, `loadAll`,
  `INITIAL_URL`)
- SP-1 persist path: `api/src/cortex_api/service/brand/` (`repo/profile_repo.py`
  atomic upsert, `service.py`, `model/profile.py`), `app/api/brand/`
- SP-2 library: `packages/brand-extract/src/cortex_brand_extract/`
  (`extract_brand_profile`, `types.py` `BrandProfile`, `extraction_meta`)
- Auth spine: `app/dependencies/{auth,brand,capability}.py`,
  `app/exception_handlers.py` (ContextMismatch → 400)
- Migration precedent + hard-won rules: `api/alembic/versions/*` (#31 head),
  `CLAUDE.md`
- Program contract decision (projection ownership): SP-2 spec
  `docs/superpowers/specs/2026-05-18-brand-extraction-engine-design.md`;
  SP-1 spec `…-sp1-brand-profile-persistence-design.md`
