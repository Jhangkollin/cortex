# SP-QUESTIONS — Real "Weekly Questions" for Onboarding Step 4 (Design)

**Date:** 2026-05-19 · **Status:** approved (brainstorm), pending spec review · **Branch:** `feat/sp-questions` (worktree `cortex-wt/sp-questions`, off `develop` @ `14069ad` — SP-MEDIA merged) · **Next:** writing-plans → subagent-driven

## 1. Problem

Onboarding **step 4 "Weekly questions"** (the questions readers are asking this week) is fully modeled. `web/src/components/onboarding-v2/step-questions.tsx` (and the 繁中 clone) read the static `LIVE_QUESTIONS` constant from `data.ts` directly — there is **no `OnboardingApi` seam method, no projection, no `loadModeled`/`page.tsx` wiring** for questions at all (more greenfield on the web side than SP-MEDIA, which already had a `getMediaNetwork` seam to swap). The displayed questions are fictional and brand-agnostic.

## 2. Goal & Non-Goals

**Goal:** Step 4 shows **real AIGC Q&A units readers actually engaged with across the Mlytics network this week**, LLM-ranked/framed for the brand, persisted and deterministic per brand — EN **and** 繁中.

**Non-goals (v1):** reader free-text query capture; translating/normalizing question text; a generalized multi-signal pipeline (Approach C — deferred, see §7); SP-VOICE (step 5, separate).

## 3. Decisions (decision log)

| # | Decision |
|---|---|
| D1 | Real source = `aigc_prod.aigc_metrics.aigc_clickstream_metrics` (the **same clean Metric View SP-MEDIA snapshots**): `question_title`, `MEASURE(question_clicks)`, `publisher_name`, `event_date` (+ `brand_uuid`/`brand_click_share` available). Validated live 2026-05-19. |
| D2 | **⊆-snapshot invariant:** an emitted question's `text` is the **verbatim real `question_title`**, `media`=real `publisher_name`, `asks`=real click volume, `when`=derived from real `event_date`. Never LLM-rewritten or translated (real zh-TW text shows as-is, incl. in the EN wizard — realness over locale purity). |
| D3 | `competitorMentions` ⊆ the brand's **real `brand_profile.competitors`** (from SP-3a analyze, via `BrandProfileRepo`). The LLM selects from that real list; it never invents competitors. |
| D4 | `intent` (∈ `Explore`/`Understand`/`Evaluate`/`Act`) and `score` (0–100 brand relevance) are **LLM-derived** (analog of SP-MEDIA's `relevance`/`why`). |
| D5 | Cost-bearing `POST` gated on `BrandCapability.EDIT_BRAND_SETTINGS`; `GET` poll on `VIEW_BRAND_DASHBOARD` (applies the SP-MEDIA @owl review #5 outcome from the start). |
| D6 | Single-source DTO (`projection.ts` `import type`s from `cortex-api.ts`) + null-safe projection (SP-MEDIA @owl #2/#3 applied from the start). |
| D7 | Web fetch uses the **d8345ff-correct wiring**: `getLiveQuestions` is fetched **post-analyze in `runAnalyze()`**, NEVER in mount-time `loadModeled`; both EN + 繁中 `page.tsx`, prop-driven `StepQuestions`; a structural call-site guard enforces it. |
| D8 | If the snapshot is empty/stale for the 7-day window → documented **LLM-synth fallback**: synth N questions grounded in the real `brand_profile` (deterministic, persisted, clearly the fallback path). |
| D9 | **Approach A** — `service/questions/` is a 1:1 clone of the merged `service/media_network/`. Reuses `BrandProfileRepo` (@owl #1) + the dbx-identifier guard (@owl #4). Future-refactor noted (§7). |

## 4. Architecture (clone of `service/media_network/`; canonical pattern = merged develop code)

### §4.1 Databricks snapshot
- Query (Metric View → `MEASURE()` + declared dims, same family as SP-MEDIA):
  ```sql
  SELECT question_title, publisher_name,
         MEASURE(question_clicks) AS clicks,
         MAX(event_date)          AS last_event_date
  FROM <catalog>.aigc_metrics.aigc_clickstream_metrics
  WHERE event_date >= dateadd(day,-7,
        (SELECT max(event_date) FROM <catalog>.aigc_metrics.aigc_clickstream_metrics))
    AND question_title IS NOT NULL AND question_title <> ''
  GROUP BY question_title, publisher_name
  ORDER BY clicks DESC
  ```
  (`<catalog>` from config, validated by the reused dbx-identifier guard.)
- Snapshot table **`weekly_question`**: `id` STRING PK = deterministic hash of `question_title|publisher_name`; `question_title` TEXT; `publisher_name` STRING; `clicks` INT; `last_event_date` DATE; `synced_at` TIMESTAMP (`server_default now()`). (No `category_hint` — the source has no per-question category column; the matcher uses the brand's category + LLM, not a per-question hint.) Upsert keyed on `id` (re-sync updates clicks/recency/synced_at). Failure-isolated (raise without upsert → prior snapshot/last-good intact). Periodic sync via a runnable entrypoint mirroring `scripts/sync_media_network.py` (own `sync_weekly_questions` function; cron entrypoint pattern shared).

### §4.2 cortex-api `service/questions/` (mirror `service/media_network/`)
- Migration (Alembic, `down_revision = e5f6a7b8c9d0`): `weekly_question` + `brand_weekly_questions` (`brand_id` UUID PK FK→`brand.id`; `status` ENUM `questionjobstatus` {pending,running,succeeded,failed}; `error` TEXT NULL; `questions` JSONB; `created_at`/`updated_at` with `server_default=sa.func.now()` + `onupdate`). Explicit `sa.Enum(name='questionjobstatus').drop(...)` in `downgrade()`. Round-trip tested.
- `QuestionsJobService` — structural mirror of `MediaNetworkJobService` (async task, dedupe, `sweep_stale`, `drain`, `cancel_all` fail-mark-before-cancel, `_run`). `_run` reads the brand profile via **`BrandProfileRepo.get(session, brand_id)`** (NOT cross-domain raw SQL), loads the `weekly_question` snapshot, calls the matcher, persists to `brand_weekly_questions`.
- **Matcher** (`questions/matcher.py`, mirror `media_network/matcher.py`): inputs = brand profile (name/category/products/competitors/about) + real `weekly_question` rows. LLM (`CORTEX_ANALYZE_*` provider) returns an ordered list; server enforces every item ⊆ snapshot (text=real `question_title`, media=real `publisher_name`, asks=real `clicks`, when=humanised real `last_event_date`). LLM adds only `intent`∈{Explore,Understand,Evaluate,Act}, `score`0–100, `competitorMentions`⊆`brand_profile.competitors`. Malformed/odd LLM payloads never raise (degrade); deterministic backfill by `clicks` desc when too few; truncate to `outlet_count`-analog (`question_count`, default 6, config). If snapshot empty → D8 LLM-synth fallback.
- DI container + `app/api/questions/` (`dto.py`, `router.py`) + `main.py` 5-edit wiring + lifespan `sweep_stale`/`cancel_all`, mirroring media. Endpoints: `POST /v1/brand/{brand_id}/weekly-questions` (202, `?regenerate`), `GET /v1/brand/{brand_id}/weekly-questions`. Gates: `active_brand` + `requires_brand_capability(EDIT_BRAND_SETTINGS)` on POST, `VIEW_BRAND_DASHBOARD` on GET.

### §4.3 Web seam (d8345ff-correct from the start)
- `OnboardingApi`: add `getLiveQuestions(): Promise<LiveQuestion[]>`. `MockOnboardingApi` → returns existing `LIVE_QUESTIONS` (mock mode unchanged). `HttpOnboardingApi` → Server Actions `startWeeklyQuestionsAction`/`pollWeeklyQuestionsAction` → endpoint; poll loop mirrors `analyzeBrand`/`getMediaNetwork` (bounded, rethrow on failed/timeout).
- `cortex-api.ts`: `startWeeklyQuestions`/`pollWeeklyQuestions` + canonical `WeeklyQuestionsDTO`/`WeeklyQuestionDTO`. `projection.ts`: `import type`s them (single source), `projectWeeklyQuestions(dto) -> LiveQuestion[]` (text←question_title, media←publisher_name, asks←clicks, when←**day-resolution** relative label from `last_event_date` — "Today"/"Yesterday"/"N days ago"; the snapshot is daily-grained so hour-level "2 hours ago" is NOT possible/used, intent/score←LLM, competitorMentions←LLM-from-real; null-safe — no misleading 0).
- Both `onboarding/v2/page.tsx` (EN) **and** `onboarding/v2/zh-TW/page.tsx` (繁中): add `liveQuestions` state; fetch in `runAnalyze()` **post-analyze in its OWN isolated `void (async () => {…})()`**, separate from the media fetch (independent failure); reset in `restart()`; pass `liveQuestions={liveQuestions}` to `<StepQuestions/>`. Make both `step-questions.tsx` prop-driven (`liveQuestions: LiveQuestion[]`), drop the `LIVE_QUESTIONS` constant import; **繁中 copy preserved**.
- Extend the structural regression guard (sibling of `orchestrator-media-callsite.test.ts`) to assert, for **both** EN+繁中 `page.tsx`: `getLiveQuestions` ∉ `loadModeled`, ∈ `runAnalyze`, after `analyzeBrand`.

### §4.4 Error handling
Matcher never raises (degrade → deterministic backfill from real snapshot; empty → D8 synth). Snapshot sync raises without upsert (prior snapshot intact). Web `getLiveQuestions` failure non-fatal and **independent of the media fetch** (separate isolated catch — refinement over SP-MEDIA's combined block). No misleading zeros (null-safe projection).

### §4.5 Testing
Mirror the SP-MEDIA suite: matcher unit (⊆-snapshot, `competitorMentions`⊆real-competitors, intent enum shape, deterministic backfill, never-raise on malformed LLM, truncation, D8 synth-on-empty); snapshot_sync unit (real-column mapping, failure-isolation); integration (repos, job dedupe/sweep, API flow + cross-tenant + **POST 403 without `EDIT_BRAND_SETTINGS`**); web (projection unit, `StepQuestions` behavioral renders real prop / not the mock constant in EN+繁中, structural call-site guard); gate parity (`api make lint`/`make test`, alembic round-trip incl. enum drop, web type-check/lint/test). Review via **`@owl review`** (the `@owl verify` workflow is infra-broken — see memory).

## 5. Security
Databricks creds only in the out-of-band sync path (never request hot path/logs); the recon PAT is throwaway — rotate after. No credentials in code/seed. Tenant scoping via `active_brand` (cross-tenant → 4xx). Real `question_title` is publisher-facing content already shown on public AIGC pages (no PII concern; not reader free-text).

## 6. Scope
SP-QUESTIONS (step 4) only. SP-VOICE (step 5) is a separate spec→plan→impl cycle.

## 7. Deferred / future-refactor (per user note)
At **SP-VOICE** (the 3rd consumer of the Databricks-snapshot + per-brand-LLM-projection spine), evaluate extracting the shared snapshot/job/matcher scaffolding (Approach B/C) — rule of three. Until then each capability context owns its pair (consistent with the codebase's per-capability-context convention). Other deferred: per-brand `brand_uuid`/`brand_click_share` prioritisation of questions on the brand's own widget activity (v1 ranks network-wide by category relevance); reader free-text capture; live Databricks on the hot path.
