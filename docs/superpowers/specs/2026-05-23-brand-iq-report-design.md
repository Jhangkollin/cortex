# Brand IQ Report — Slice 1: Backend report-generation API (COR-79)

- **Status**: Draft for review
- **Date**: 2026-05-23
- **Epic**: COR-78 · **Story**: COR-79
- **Branch**: `feature/cor-79-brand-report-api`
- **Source design**: `brand-report/Engineering Handoff.md` + `brand-report/data.jsx` (`BRAND_IQ`) from the Claude Design handoff bundle

## 1. Context & scope

After a brand finishes onboarding, the brand-agent analysis (the `cortex_brand_extract` pipeline) has already populated several brand-scoped tables in cortex-api's Postgres. The Brand IQ Report turns that persisted analysis into a single versioned document — the `BRAND_IQ` JSON contract — that downstream slices render as a PDF (COR-80), an in-app viewer (COR-81), and the three dashboard entry points (COR-82, COR-83).

**This slice (COR-79) builds only the backend contract and its generation:** a new `brand_report` domain that assembles, persists (versioned), and serves the report JSON via an async generate + poll + version-list API. It does **not** include PDF rendering or any web UI.

### In scope
- New `service/brand_report/` domain (mirrors `service/brand_identity/`) + `app/api/brand_report/`.
- `brand_report` table + Alembic migration.
- Async generation job mirroring `service/brand`'s `AnalyzeJobService` (`BackgroundTaskTracker` + stale sweep + graceful cancel).
- Report assembly: read 4 brand-scoped tables → compose the `BRAND_IQ` `ReportDTO`; honesty markers for absent sections.
- LLM synthesis of `insights` + `risks` (+ narrative connective strings) using the existing provider (`AnalyzeConfig` / `build_provider` / `LLMProvider.complete_json`).
- Unit + integration tests in the same PR.

### Out of scope (other stories)
- PDF rendering / download (COR-80).
- Report Viewer, celebration modal, hero card, Knowledge Base UI (COR-81/82/83).
- Onboarding auto-trigger wiring (COR-82). This slice exposes the `POST` endpoint; callers come later. Manual/testing invocation is sufficient here.
- A dedicated `VIEW_BRAND_REPORT` capability — we reuse `VIEW_BRAND_DASHBOARD` (see §9).

## 2. Goals / non-goals

**Goals**
1. A stable `BRAND_IQ` JSON contract (frozen Pydantic `ReportDTO`) that slices 2–5 consume unchanged.
2. Every present section sourced from real persisted onboarding data; every absent section honestly marked `資料不足` — never blank, never fabricated.
3. Async generation that survives restarts (stale-job reclaim) and shuts down cleanly.
4. Versioned snapshots: regenerating archives the prior current report.

**Non-goals**
- Real-time/streaming generation. Poll-based is fine.
- Cross-brand or org-level reports. Strictly `brand_id`-scoped.
- Backfilling onboarding data. If a source table is empty, the corresponding section is `資料不足`.

## 3. Architecture

New domain following the canonical write-side layout. The only SQLModel is the thin `brand_report` envelope; the report payload itself is an **immutable frozen Pydantic VO** (`ReportDTO`) serialized into a JSONB column — a CQRS read-model snapshot, per CLAUDE.md's "don't conflate SQLModel with read VOs" rule.

```
api/src/cortex_api/
  app/api/brand_report/
    __init__.py
    router.py            # 3 endpoints, auth via Depends
    dto.py               # request/response DTOs + the ReportDTO contract (re-exported)
  service/brand_report/
    __init__.py
    config.py            # Config(BaseSettings, env_prefix="CORTEX_BRAND_REPORT_")
    container.py         # DI wiring (provider reused from brand domain)
    service.py           # BrandReportService (read/list/orchestrate)
    job_service.py       # BrandReportJobService (async generate, sweep, cancel)
    composer.py          # BrandReportComposer.compose(sources, provider) -> ReportDTO; LLM synthesis lives here (provider injected, pure module)
    contract.py          # frozen Pydantic ReportDTO mirroring BRAND_IQ
    model/
      __init__.py
      report.py          # SQLModel brand_report table + BrandReportStatus enum
    repo/
      __init__.py
      report_repo.py     # CRUD + versioning on brand_report
```

`main.py` is the only place that changes outside this domain: instantiate the container, wire the router module, include the router, register the stale-sweep entry, and cancel on shutdown.

## 4. Data model

### `brand_report` table (SQLModel)

| column | type | constraints / notes |
|---|---|---|
| `id` | UUID | PK, default `core.identifiers.uuid7()` |
| `brand_id` | UUID | FK → `brand.id`, indexed |
| `report_id` | str(64) | human id `BIQ-{YYYY-MM-DD}-{CODE}`; `CODE` = first 6 uppercase alnum of brand name; indexed |
| `version` | str(16) | `v1.0`, `v1.1`, … (minor bump per regeneration) |
| `status` | enum `brandreportstatus` | `generating｜ready｜failed` |
| `report_json` | JSONB | nullable until `ready`; the serialized `ReportDTO` snapshot |
| `cost_usd` | float | nullable; summed LLM cost |
| `error` | str | nullable; failure reason |
| `archived_at` | datetime | nullable; set when superseded by a newer `ready` report |
| `created_at` | datetime | `server_default=sa.func.now()` |
| `updated_at` | datetime | `server_default=sa.func.now()`, `onupdate=sa.func.now()` |

- **Current report** for a brand = the row with `status='ready'` and `archived_at IS NULL`. Enforced in app logic (the job archives the prior current row in the same transaction it marks the new one ready).
- `status` exposes the spec's vocabulary (`generating/ready/failed`) directly, rather than reusing the brand-analysis `pending/running/succeeded/failed` enum — the public contract in the handoff is `generating｜ready｜failed`.

### Migration
- New Alembic revision after current head; `down_revision` chained correctly.
- `created_at`/`updated_at` server defaults + `updated_at onupdate` (per CLAUDE.md hard rule #1).
- Explicit ENUM drop in `downgrade()`: `sa.Enum(name='brandreportstatus').drop(op.get_bind(), checkfirst=True)` (hard rule #2).
- Round-trip tested: `upgrade head → downgrade base → upgrade head` (hard rule #3).
- `alembic/env.py` **must** import the new `brand_report` model so autogenerate detects the table (required for a new table, not optional).

## 5. The report contract (`ReportDTO`)

Frozen Pydantic v2 models mirroring `BRAND_IQ` field-for-field. This is the **public contract**; slices 2–5 depend on it. Field names match `data.jsx` exactly (camelCase preserved via `alias`/`model_config` so the JSON matches the prototype the UI already expects).

```
ReportDTO
  meta: ReportMeta
  core: list[CoreItem]              # {item, body, certainty}
  coreJudgement: str
  productLines: list[ProductLine]   # {line, thesis, examples, signal, confidence}
  productNote: str
  subBrands: list[SubBrand]         # {type, name, note}
  endorsements: SectionStatusBody   # {status, body}
  ipCollabs: SectionStatusBody      # {status, body}
  mediaNetwork: list[MediaOutlet]   # {name, audience, weekly, relevance, topics, trend}
  competitors: list[CompetitorTier] # {tier, brands, basis, position}
  competitorNote: str
  insights: Insights                # {confirmed[], inferences[], hypotheses[]}
  faq: list[FaqItem]                # {q, a, source, level}
  channels: list[Channel]           # {type, surfaces, read}
  risks: list[Risk]                 # {theme, trigger, where, note, level, action}
  sources: Sources                  # {A[], B[], C[]}
  quality: Quality                  # {high, midLow, gaps, conflicts, open}
```

`SectionStatusBody.status` uses the literal `"資料不足"` for absent sections (or `"已確認"｜"高可能"` when evidence exists), matching the handoff's honesty contract.

## 6. Report assembly (`BrandReportComposer`)

Reads all source tables by `brand_id` PK via injected repos (reusing the existing domain repos — `BrandProfileRepo`, `BrandMediaRepo`, `BrandQuestionsRepo` — so we never duplicate read logic). An async function of `(sources, provider) → ReportDTO`: LIVE sections are pure mappings; the LLM-synthesized sections take the injected `provider`. Trivially testable with fake repos + a fake provider.

> **Voice source (resolved):** slice 1 reads `brand_profile.voice_samples` (`list[dict]`, the raw extracted samples) for the `core` Brand Voice item and `risks` synthesis. The separate `brand_voice.samples` (`dict[str, str]`, curated tone keyed by style, via `BrandVoiceRepo`) is a different artifact and is **out of scope** for slice 1 — so `BrandVoiceRepo` is not a dependency here.

### Section → source mapping

| Section | Source | Rule |
|---|---|---|
| `meta` | `brand_profile` (+ analysis job, clock) | `subject/enName=name`, `legalName`, `domain`, `monogram`, `brandColor`, `tagline`, `founded`, `category=category_value`, `confidence=category_confidence`, `primaryMarket/extendedMarkets` from `region`, `reportDate=today`, `window=[today-1y, today]`, `reportId`, `pageCount=8`, `preparedBy` from config |
| `core` | `brand_profile` scalars + `brand_profile.voice_samples` | derived items with `certainty` from `category_confidence` band; Brand Voice item from `brand_profile.voice_samples` (`list[dict]`, raw extracted samples) |
| `productLines` | `brand_profile.products` | map `name→line`, `category→thesis`, `url/examples`, `confidence` |
| `subBrands` | `brand_profile` name + product names | main brand + product series rows; IP/聯名 row → `資料不足` (no source) |
| `endorsements` | — | `資料不足` (no source) |
| `ipCollabs` | — | `資料不足` (no source) |
| `mediaNetwork` | `brand_media_network.outlets` | map outlet `name/relevance/wau→weekly`; `audience/topics/trend` if present else omit |
| `competitors` | `brand_profile.competitors` | group by tier; `name→brands`, `match_score` informs `basis` |
| `faq` | `brand_weekly_questions.questions` | persisted item keys are `{id, text, media, asks, when, intent, score, competitorMentions}`: `text→q`, `media→source`, `intent`/`score`→`level`. **No persisted answer** → `a` is produced by the synthesis LLM call grounded in `products`/`brand_profile`, else `資料不足` |
| `channels` | derived from `mediaNetwork` + `brand_profile` | D2C from domain; media-network channel from outlets; physical/overseas → `資料不足` where unknown. Prefer `brand_media_network.outlets` over the raw `brand_profile.media_matches` snapshot (both exist and are written; outlets is the richer brand-scoped result) |
| `sources` | `brand_profile.source_url` + `extraction_meta` | A = official URLs; B = media/competitor matches; C = caveat |
| `quality` | `extraction_meta` + `brand_profile_analysis_job` | tier/model/warnings/cost → quality bands |
| `coreJudgement`, `productNote`, `competitorNote` | **LLM** | short synthesis strings over the structured data |
| `insights` | **LLM** | `{confirmed, inferences, hypotheses}` synthesized from all sections |
| `risks` | **LLM** | risk list synthesized from `brand_profile.voice_samples` (raw sample text) + product copy |

### Honesty rule (enforced, tested)
Any section whose source table is empty/absent yields a `資料不足` marker (string status or an empty list paired with a `資料不足` note), never a blank or invented value. Covered by explicit unit tests.

## 7. LLM synthesis (insights / risks / notes)

Reuses the existing provider stack — **no new config, no infra changes, no direct `anthropic` import** (`cortex-brand-extract` already vendors the SDK and is an editable dep of `api/`).

- Config: reuse `AnalyzeConfig` (`env_prefix="CORTEX_ANALYZE_"`, default `model="claude-opus-4-7"`, key server-managed).
- Provider: `build_provider(analyze_config)` as a container singleton, injected into `BrandReportJobService`, which passes it to `BrandReportComposer.compose(...)`. This matches the voice/questions structure where `complete_json` lives in a pure module (`generator.py`/`matcher.py`) with the provider passed through — keeping the §12 testability story (fake provider) intact.
- Call: `await provider.complete_json(system=..., user=..., schema=...)` → `LLMResult{data, cost_usd, ...}`. One call for `insights` (+ the narrative `coreJudgement`/`productNote`/`competitorNote` and the grounded `faq` answers ride along in its schema to save calls), one call for `risks`. Validate `result.data` into the Pydantic section model; on `ValidationError`, retry once with the error appended to the prompt (existing repair pattern), else fail.
- Cost: sum `result.cost_usd` across calls → persist on `brand_report.cost_usd`. (Note: `service/voice` and `service/questions` receive `LLMResult` but discard cost; persisting it here is intentional new behavior — `LLMResult.cost_usd` is a real field on the result.)
- Errors: catch `cortex_brand_extract.errors.UpstreamError/UpstreamTimeoutError` → re-raise as `core.exceptions.UpstreamError/UpstreamTimeoutError` (chained `from e`); job marked `failed`.
- Honesty under LLM: prompts are grounded strictly in the supplied structured data and instructed not to invent; if the LLM returns nothing usable for a section it degrades to `資料不足`, not fabrication.

> Tradeoff noted: two Opus calls put report generation in the multi-second range, so the handoff's "ready within ~5s" is best-effort. `estimatedSeconds` in the 202 response reflects this; the poll contract decouples the client from exact timing.

## 8. API surface

All under the brand scope, auth via FastAPI `Depends` (no middleware):

### `POST /v1/brand/{brand_id}/report` → 202
```json
{ "reportId": "BIQ-2026-05-23-ACMEBA", "status": "generating",
  "estimatedSeconds": 8, "pollUrl": "/v1/brand/{brand_id}/report/BIQ-..." }
```
Inserts a `generating` row, spawns `job_service.generate(brand_id, report_pk)` via `BackgroundTaskTracker`, returns immediately.

### `GET /v1/brand/{brand_id}/report/{report_id}` → 200
- `ready` → the full `ReportDTO` JSON (`report_json`).
- `generating` / `failed` → status envelope `{reportId, status, error?}`.
- unknown `report_id` for this brand → 404.

### `GET /v1/brand/{brand_id}/reports` → 200
Version history: `[{reportId, version, createdAt, status: "current"｜"archived", cost_usd}]`, newest first.

### Auth (all three)
`tenant: BrandTenantCtx = Depends(active_brand)` + `_: None = Depends(requires_brand_capability(BrandCapability.VIEW_BRAND_DASHBOARD))`. `active_brand` already asserts the JWT `active_context.kind=="brand"` and that the claim id matches the URL `brand_id`; client-supplied scope is never trusted.

## 9. Design decisions & alternatives

- **Reuse `VIEW_BRAND_DASHBOARD`** rather than a new `VIEW_BRAND_REPORT` capability. Capabilities are baked into the JWT at login by the policy classes; a new capability needs policy changes + token re-issue plumbing for zero functional gain right now. Revisit if report access must diverge from dashboard access.
- **Status enum `generating/ready/failed`** (not the analysis job's `pending/running/succeeded/failed`) to match the handoff's public contract directly and avoid leaking internal job vocabulary into the API.
- **Snapshot the whole `ReportDTO` into JSONB** rather than normalizing sections into tables. The report is an immutable, point-in-time read model; versioning + downstream consumption want the whole document atomically. Normalizing would add churn for no query benefit.
- **Composer reads existing domain repos** instead of new queries — single source of truth for each table's read shape; the report is an aggregator, not a new owner.
- **Versioning = new row + archive prior.** Simple, auditable, matches the KB version-history UI (COR-83). Minor-bump (`v1.x`) per regeneration.

## 10. Error handling

- Source profile missing (brand never onboarded) → `NotFoundError` from the service before scheduling a job (no empty report). Maps to 404/409 at the router per existing convention.
- LLM upstream failure/timeout → job `failed` with `error`; `GET` returns the failed envelope (the dashboard later shows a retry — COR-82).
- Stale `generating` rows (process died mid-run) → reclaimed by the sweep loop after `stale_job_seconds`, marked `failed` so the client stops polling.
- All raised exceptions originate from `core/exceptions.py` and chain with `from e` (CLAUDE.md).

## 11. Config

New `service/brand_report/config.py`:
```
Config(BaseSettings, env_prefix="CORTEX_BRAND_REPORT_")
  estimated_seconds: int = 8
  stale_job_seconds: int = 900
  page_count: int = 8
  prepared_by: str = "Cortex · Brand Agent"
```
LLM config is **not** duplicated — `AnalyzeConfig` (`CORTEX_ANALYZE_*`) is reused.

## 12. Testing (same PR)

**Unit** (`tests/unit/...`, DI provider overrides, not `mock.patch`):
- Composer maps each LIVE section from fake repo data (one test per section family).
- Honesty: empty source → `資料不足` for `subBrands` IP row, `endorsements`, `ipCollabs`, and any empty LIVE source.
- LLM sections: fake `LLMProvider` returning canned `data`; assert `insights`/`risks` parsed + cost summed; `ValidationError` → one repair retry → success/failure.
- `report_id` format + `version` increment + prior-current archival.
- Status mapping (`generating/ready/failed`).

**Integration** (`integration` marker, docker-compose Postgres):
- `POST` → 202; poll `GET` → eventually `ready` with contract-shaped JSON (LLM provider overridden via container to a deterministic fake).
- `GET` unknown report → 404.
- Auth: JWT for a different brand → 403; missing capability → 403.
- `GET /reports` returns current + archived after a regeneration.
- Migration round-trip test.

## 13. Conventions checklist
- Three-tier DI; container wired only in `main.py`.
- `structlog.get_logger(__name__)` assigned in `__init__`.
- Exceptions only from `core/exceptions.py`, chained `from e`.
- Pydantic v2 DTOs/config; SQLModel only for the `brand_report` envelope.
- Two-tier config prefix (`CORE_*` untouched; service uses `CORTEX_BRAND_REPORT_*`, reuses `CORTEX_ANALYZE_*`).
- uuid7 ids; server-default timestamps; explicit ENUM drop on downgrade.

## 14. Implementation order (for the plan)
1. `contract.py` (`ReportDTO`) + unit tests for the contract shape.
2. `model/report.py` + migration + round-trip test.
3. `repo/report_repo.py` (CRUD + versioning) + integration test.
4. `composer.py` (LIVE sections + honesty) + unit tests (no LLM yet).
5. LLM synthesis in composer/job (`insights`/`risks`/notes) + unit tests with fake provider.
6. `job_service.py` (async generate + sweep + cancel) + `service.py`.
7. `config.py` + `container.py`.
8. `app/api/brand_report/{router,dto}.py` + auth.
9. `main.py` wiring (container, router, sweep entry, shutdown cancel).
10. Integration tests (HTTP generate→poll→ready, 404, auth, version list).
11. `ruff` + `mypy` clean; full `pytest`.

---

## Implementation addenda (post-build, accepted in final review)

Deviations from the §4/§8 examples, made during implementation — recorded so downstream slices (COR-80/81/83) consume the *actual* contract:

1. **`report_id` format** = `BIQ-{YYYY-MM-DD}-{CODE}-{uuid8}` (e.g. `BIQ-2026-05-24-ACME-1a2b3c4d`), not `BIQ-{date}-{CODE}`. The uuid8 suffix (from the row's uuid7 PK) guarantees uniqueness within a brand across same-day regenerations/retries — a same-day *failed* attempt would otherwise recompute an identical id. `meta.reportId` equals the `brand_report.report_id` column (single source, asserted in tests).
2. **`ReportVersionItem` shape** (`GET /v1/brand/{id}/reports`) = `{reportId, version, createdAt, status, current, costUsd}`, where `status` is the raw `generating|ready|failed` and `current: bool = (status == ready and archived_at is None)`. This supersedes the spec's `status: "current"|"archived"` with a more informative shape; the KB version-history UI (COR-83) derives the "現行 / archived" badge from `current`.
3. **Auth error codes**: cross-brand JWT (URL brand ≠ claim id) → **400** (`ContextMismatchError`); missing capability → **403** (`ForbiddenError`). (Spec §12's "different brand → 403" was imprecise — 403 is the missing-capability case.)
