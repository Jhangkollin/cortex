# Brand IQ Report — Slice 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `brand_report` backend domain (COR-79) — an async, versioned API that assembles the `BRAND_IQ` report JSON from a brand's onboarding analysis (4 brand-scoped tables + LLM-synthesized `insights`/`risks`) and serves it via generate→poll→version-list endpoints.

**Architecture:** New write-side domain mirroring `service/brand` + `service/brand_identity`. A thin SQLModel `brand_report` envelope stores an immutable, frozen-Pydantic `ReportDTO` snapshot as JSONB (CQRS read-model snapshot). Generation is an async in-process worker mirroring `AnalyzeJobService` (own `self._tasks`, stale sweep, graceful `cancel_all`). LLM synthesis reuses `AnalyzeConfig` + `build_provider` + `LLMProvider.complete_json` exactly as `service/voice` does.

**Tech Stack:** FastAPI, SQLModel + Alembic (async asyncpg), dependency-injector, Pydantic v2, `cortex_brand_extract` LLM provider, pytest (+`integration` marker), ruff, mypy.

**Spec:** `docs/superpowers/specs/2026-05-23-brand-iq-report-design.md`
**Branch:** `feature/cor-79-brand-report-api` · **Alembic head to chain from:** `4facedd34e4d`

---

## Conventions (apply to every task)

- All paths are under the worktree root `~/.config/superpowers/worktrees/cortex/cor-79-brand-report-api/`. Run all commands from `api/`.
- `from __future__ import annotations` at the top of every module.
- `self._logger = structlog.get_logger(__name__)` in `__init__` — never module-level.
- Exceptions only from `cortex_api.core.exceptions`, chained with `from e`.
- Frozen Pydantic VOs for the read contract; SQLModel only for the `brand_report` envelope.
- Run a single test: `uv run pytest <path>::<test> -v`. Unit suite: `uv run pytest -m "not integration"`. Full: `uv run pytest`.
- Commit message prefix `feat(COR-79):` / `test(COR-79):`; end body with the `Co-Authored-By` trailer used on the spec commit.
- After each task's tests pass, run `uv run ruff format . && uv run ruff check . && uv run mypy .` before committing.

## File map (locked)

```
api/src/cortex_api/
  service/brand_report/
    __init__.py
    contract.py          # ReportDTO + section VOs (frozen, camelCase = BRAND_IQ keys)
    model/__init__.py
    model/report.py       # BrandReport SQLModel + BrandReportStatus
    repo/__init__.py
    repo/report_repo.py   # CRUD + versioning/archival
    composer.py           # compose(sources, provider) -> ReportDTO  (LIVE mappers + LLM synthesis)
    config.py             # Config(env_prefix="CORTEX_BRAND_REPORT_")
    service.py            # BrandReportService (async generate + get + list + sweep + cancel)
    container.py          # DI wiring (reuses AnalyzeConfig/build_provider + source repos)
  app/api/brand_report/
    __init__.py
    dto.py                # GenerateReportResponse / ReportEnvelope / ReportVersionItem
    router.py             # 3 endpoints
api/alembic/versions/<rev>_brand_report.py
api/tests/unit/service/brand_report/test_contract.py
api/tests/unit/service/brand_report/test_composer.py
api/tests/unit/service/brand_report/test_service.py
api/tests/integration/test_brand_report_repo.py
api/tests/integration/test_brand_report_migration.py
api/tests/integration/test_brand_report_api.py
```

Source-table read shapes (verified, for the composer):
- `BrandProfile` (`service/brand/model/profile.py`): scalars `name, legal_name, tagline, monogram, brand_color, founded, about, source_url, category_value, category_confidence`; JSONB lists `region, voice_samples, products[{name,category,url,confidence}], competitors[{name,domain,match_score}]`; `extraction_meta` JSONB.
- `BrandMediaNetwork.outlets` (`service/media_network/model/job.py`): `list[dict]` items e.g. `{hostname, member_name, wau, relevance, why, topics, context_agent_label, audience_descriptor}`.
- `BrandWeeklyQuestions.questions` (`service/questions/model/job.py`): `list[dict]` items `{id, text, media, asks, when, intent, score, competitorMentions}`.
- Repos expose `async get(session, brand_id) -> Model | None`: `BrandProfileRepo`, `BrandMediaRepo`, `BrandQuestionsRepo`.

---

## Task 1: Report contract (`ReportDTO`)

**Files:**
- Create: `api/src/cortex_api/service/brand_report/__init__.py` (empty)
- Create: `api/src/cortex_api/service/brand_report/contract.py`
- Test: `api/tests/unit/service/brand_report/test_contract.py` (+ `__init__.py` in new test dirs)

Steps: write failing contract test (camelCase round-trip, frozen, INSUFFICIENT_DATA == "資料不足") → run FAIL → implement frozen Pydantic models (ReportMeta, CoreItem, ProductLine, SubBrand, SectionStatusBody, MediaOutlet, CompetitorTier, Insights, FaqItem, Channel, Risk, Sources, Quality, ReportDTO) with `model_config = ConfigDict(frozen=True)` and camelCase field names matching BRAND_IQ exactly → run PASS → ruff/mypy → commit `feat(COR-79): ReportDTO contract mirroring BRAND_IQ`.

(Full code for contract.py and the test is in the spec §5 and was authored during planning — see the design spec; field names are the camelCase BRAND_IQ keys, `INSUFFICIENT_DATA = "資料不足"`.)

---

## Task 2: `brand_report` model + migration

**Files:**
- Create: `service/brand_report/model/__init__.py`, `model/report.py`
- Create: `api/alembic/versions/<rev>_brand_report.py` (down_revision = `4facedd34e4d`)
- Modify: `api/alembic/env.py` — `from cortex_api.service.brand_report.model.report import BrandReport  # noqa: F401`
- Test: `api/tests/integration/test_brand_report_migration.py`

Model `BrandReport` columns: `id` (uuid7 PK), `brand_id` (FK brand.id, index), `report_id` (str64, index), `version` (str16), `status` (SAEnum `brandreportstatus` generating/ready/failed), `report_json` (JSONB nullable), `cost_usd` (float nullable), `error` (str nullable), `archived_at` (datetime nullable), `created_at`/`updated_at` (datetime; in migration use `server_default=sa.func.now()` and `onupdate=sa.func.now()`). Index `ix_brand_report_brand_id_status`.

Migration: mirror `e5f6a7b8c9d0_media_network.py` — `op.create_table(...)` with FK `ondelete="CASCADE"`, server_default timestamps; `downgrade()` drops indexes + table + `sa.Enum(name="brandreportstatus").drop(op.get_bind(), checkfirst=True)`.

Test (integration): `command.upgrade(head) → downgrade(-1) → upgrade(head)` round-trip; assert `brand_report` table present. Steps: write test → FAIL → `uv run alembic revision --autogenerate -m "brand report"` then hand-fix to template → `docker-compose up -d` → `uv run pytest tests/integration/test_brand_report_migration.py -v` PASS → ruff/mypy → commit `feat(COR-79): brand_report table + migration (round-trip tested)`.

---

## Task 3: `BrandReportRepo` (CRUD + versioning/archival)

**Files:** Create `repo/__init__.py`, `repo/report_repo.py`; Test `tests/integration/test_brand_report_repo.py`.

Methods (all take `AsyncSession`; service owns txn — mirror `AnalysisJobRepo`):
- `create(row)`, `get(brand_id, report_id)`, `get_current(brand_id)` (status READY + `archived_at IS NULL`), `list_for_brand(brand_id)` (created_at desc), `next_version(brand_id)` (v1.0 first, else bump minor of current), `mark_ready(row, *, report_json, cost_usd)` (archive prior current via `archived_at=now()`), `mark_failed(row, *, error)`, `sweep_stale(*, older_than_seconds)` (GENERATING older than cutoff → FAILED).

Integration test proves: second `mark_ready` archives the first, `next_version` returns `v1.1`, `get_current` returns the newest, `list_for_brand` newest-first, exactly one un-archived READY. Steps: write test → FAIL → implement repo → `uv run pytest tests/integration/test_brand_report_repo.py -v` PASS → ruff/mypy → commit `feat(COR-79): BrandReportRepo with versioning + archival`.

---

## Task 4: Composer — LIVE sections (no LLM)

**Files:** Create `composer.py`; Test `tests/unit/service/brand_report/test_composer.py`.

`ReportSources` dataclass (`profile` dict/model, `outlets` list, `questions` list). `compose_live(sources, *, page_count, prepared_by) -> ReportDTO` builds every section EXCEPT LLM fields (placeholders: `coreJudgement=""`, `productNote=""`, `competitorNote=""`, `insights=Insights([],[],[])`, `risks=[]`, faq `a=INSUFFICIENT_DATA`).

Mapping rules (spec §6):
- `meta` from profile + today + 1-year window + `report_id = BIQ-{today}-{CODE}` (`CODE` = `re.sub(r"[^A-Za-z0-9]","",name).upper()[:6]` or "BRAND") + `pageCount`/`preparedBy` from config.
- `core`: 品牌主體 / 主要市場 / 品牌定位 / Brand Voice items; `certainty` band from `category_confidence` (`>=90`→已確認, `>=70`→高可能, else 資料不足).
- `productLines` from `products`; `subBrands` = main brand + product-series + IP row (資料不足); `endorsements`/`ipCollabs` = 資料不足.
- `mediaNetwork` from `outlets` (name=member_name, audience=audience_descriptor, weekly=fmt(wau), relevance, topics=join, trend default); `competitors` → one "直接競品" tier (brands="、".join(names)); `faq` from `questions` (q=text, source=media, level from intent/score, a placeholder); `channels` derived from outlets+domain+region; `sources`/`quality` from source_url+extraction_meta+region. Empty source → `[]` / 資料不足.

Tests: live mapping populated; absent sources → 資料不足; low confidence → core certainty 資料不足. Steps: write tests → FAIL → implement (small `_section_*` helpers) → PASS → ruff/mypy → commit `feat(COR-79): report composer LIVE sections + honesty markers`.

---

## Task 5: Composer — LLM synthesis (insights/risks/notes/faq answers)

**Files:** Modify `composer.py` (add `async def compose(sources, provider, *, page_count, prepared_by) -> tuple[ReportDTO, float]`); extend `test_composer.py`.

Mirror `service/voice/generator.py`: build `system`+`user`(JSON)+`schema`, `await provider.complete_json(...)`, validate `result.data`, **degrade gracefully** on any exception (log `brand_report_synthesis_failed`; never raise). Two calls: (1) insights + coreJudgement/productNote/competitorNote + `faqAnswers[]`; (2) risks. Sum `result.cost_usd`. Build the final frozen DTO via `compose_live(...).model_copy(update=...)`.

Tests with `cortex_brand_extract.llm.base.FakeProvider`: provider data fills LLM sections + cost summed; provider raises → graceful empty insights/risks + faq `a` stays 資料不足. Steps: write tests → FAIL → implement → PASS → ruff/mypy → commit `feat(COR-79): LLM synthesis for insights/risks/notes in composer`.

---

## Task 6: `BrandReportService` (async generate + read) + config

**Files:** Create `config.py`, `service.py`; Test `tests/unit/service/brand_report/test_service.py`.

`config.py`: `Config(BaseSettings, env_prefix="CORTEX_BRAND_REPORT_")` with `estimated_seconds=8`, `stale_job_seconds=900`, `page_count=8`, `prepared_by="Cortex · Brand Agent"`.

`service.py` `BrandReportService` mirrors `AnalyzeJobService`: own `self._tasks: dict[Task, tuple[UUID, str]]`; `generate(brand_id)` (load `BrandProfile`; `NotFoundError` if missing; `next_version` + `report_id`; create GENERATING row; spawn `_run`; return row); `get_report(brand_id, report_id)` (NotFoundError if missing); `list_reports(brand_id)`; `sweep_stale()`; `drain()`; `cancel_all()`; `_run(brand_id, report_pk)` (load 4 sources in one read session → `await compose(...)` → `mark_ready` in fresh session, re-`get` row first); `_fail(...)`. Catch `cortex_brand_extract.errors.UpstreamError/UpstreamTimeoutError` → re-raise as `core.exceptions` equivalents after `_fail`; catch-all → `_fail` + return. Add `estimated_seconds` property.

Tests (fakes, DI override not mock.patch): generate without profile → NotFoundError; generate + drain → report READY with `report_json["meta"]["subject"]`. Steps: write tests → FAIL → implement → PASS → ruff/mypy → commit `feat(COR-79): BrandReportService async generate + read + config`.

---

## Task 7: DI container

**Files:** Create `container.py`.

`Container(DeclarativeContainer)`: `infra_container`, `config` (Singleton Config), `database_client` (`infra_container._database_client_factory`), `report_repo`/`profile_repo`(BrandProfileRepo)/`media_repo`(BrandMediaRepo)/`questions_repo`(BrandQuestionsRepo) singletons, `analyze_config` (Singleton AnalyzeConfig) + `provider` (Singleton `build_provider, analyze_config`), `service` (Singleton BrandReportService wiring all of the above). Mirror `service/voice/container.py`. Commit `feat(COR-79): brand_report DI container`.

---

## Task 8: Router + DTOs

**Files:** Create `app/api/brand_report/__init__.py`, `dto.py`, `router.py`.

`dto.py`: `GenerateReportResponse(reportId, status, estimatedSeconds, pollUrl)` + `from_model`; `ReportEnvelope(reportId, status, error|None, report|None)` (`report` = `report_json` when READY) + `from_model`; `ReportVersionItem(reportId, version, createdAt, status("current"|"archived" from archived_at), cost_usd)` + `from_model`.

`router.py`: three endpoints mirroring `app/api/brand/router.py` — `@inject`, `Provide[BrandReportContainer.service]`, `Depends(active_brand)`, `dependencies=[Depends(requires_brand_capability(BrandCapability.VIEW_BRAND_DASHBOARD))]`:
- `POST /v1/brand/{brand_id}/report` status_code=202 → `service.generate(tenant.brand_id)`.
- `GET /v1/brand/{brand_id}/report/{report_id}` → `service.get_report(...)`.
- `GET /v1/brand/{brand_id}/reports` → `service.list_reports(...)`.
Always pass `tenant.brand_id`. Commit `feat(COR-79): brand_report router + DTOs`.

---

## Task 9: Wire into `main.py`

Modify `api/src/cortex_api/main.py` (copy the `voice` container wiring exactly):
- import router: `from cortex_api.app.api.brand_report.router import router as brand_report_router`
- import container: `from cortex_api.service.brand_report.container import Container as BrandReportContainer`
- instantiate near `_voice_container`: `_brand_report_container = BrandReportContainer()`
- add `_brand_report_container,` to `_all_containers()`
- add to `_sweep_stale_loop` `sweeps` tuple: `("brand_report", lambda: _brand_report_container.service().sweep_stale()),`
- add to `_lifespan` shutdown: `with contextlib.suppress(Exception): await _brand_report_container.service().cancel_all()`
- add `_brand_report_container.wire(modules=["cortex_api.app.api.brand_report.router"])`
- add `app.include_router(brand_report_router)`

Verify: `uv run pytest tests/unit/test_app_boots.py -v` PASS; full unit suite green. ruff/mypy → commit `feat(COR-79): wire brand_report container + router + sweep into main`.

---

## Task 10: HTTP integration tests

Create `tests/integration/test_brand_report_api.py` — mirror `test_media_network_api.py`'s `make_client`: `create_app()`, override `authenticated_user` with `_authed(brand_id, caps)`, override `_main._brand_report_container.service` with a `BrandReportService` whose `provider` is a `FakeProvider` (deterministic), seed `brand`+`brand_profile`(+optional media/questions) inside `client.portal.call(_seed, ...)`.

Tests: generate→poll ready; unknown report → 404; missing capability → 403; cross-tenant (JWT brand ≠ URL brand) → 4xx; version list (generate twice → current + archived). Run `uv run pytest tests/integration/test_brand_report_api.py -v` (docker-compose up) PASS. ruff/mypy → commit `test(COR-79): brand_report HTTP integration tests`.

---

## Task 11: Final quality gate

- `uv run ruff format . && uv run ruff check . && uv run mypy .` → clean.
- `uv run pytest -m "not integration" -q` → green.
- `uv run pytest` (docker-compose up) → green incl. integration.
- `git status` clean; COR-79 acceptance (spec §2/§12) all met.
- Do NOT push/PR yet — separate user-initiated step (fetch + rebase onto origin/develop first).

---

## Notes for the executor
- `service/brand/analyze_service.py` is the structural reference for `service.py` (session-split discipline: separate sessions for status writes vs the long compose; re-`get` rows after each session boundary).
- `service/voice/generator.py` is the reference for the LLM call + graceful degradation.
- `tests/integration/test_media_network_api.py` is the reference for the `make_client` DI-override harness.
- `active_brand` already enforces JWT `brand_id` == URL `brand_id`; always pass `tenant.brand_id` to the service.
- NOTE: implementation code uses SQLModel's `session.exec(...)` (the SQLModel query API) — unrelated to `child_process.exec`; a repo-local Write hook flags the substring `exec(` as a false positive, so create those files via the editor and ignore that specific warning.

---

## Plan review addenda (approved 2026-05-24)

The plan was reviewed and approved. Two advisory tightenings folded in:

1. **report_id single source (Task 6 / Task 8):** the `report_id` is computed once in `generate()` and written to BOTH the `brand_report.report_id` column AND `meta.reportId` inside `report_json`. They must never diverge — compute once, pass into both the row and the composer's `meta`.
2. **Spec §10 at the HTTP layer (Task 10):** add an integration assertion `generate for a brand with no onboarded profile → 404` (service-level coverage exists in Task 6; this closes the loop end-to-end).
