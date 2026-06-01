# SP-MEDIA — Real Media Network for Onboarding Step 3

**Status:** Approved design (brainstorm complete 2026-05-19). Ready for implementation plan.
**Owner program:** "Make onboarding steps 3/4/5 real" (decomposed into SP-MEDIA → SP-QUESTIONS → SP-VOICE; this spec covers **SP-MEDIA only**).
**Pattern source:** mirrors the merged SP-3a analyze pipeline (`docs/superpowers/specs/2026-05-18-sp3a-analyze-pipeline-design.md`).

---

## 1. Problem

Onboarding **step 3 "Media network"** (`web/src/components/onboarding-v2/step-media.tsx`, fed by `MEDIA_NETWORK` constants via the `OnboardingApi` seam) shows static mock outlets ("MoneyDJ", "Smart Wealth Monthly", …) and fabricated reach numbers, identical for every brand. It must become real and brand-specific.

## 2. Goal / Non-goals

**Goal:** Step 3 shows a brand-relevant ranking of **real Mlytics network publishers** with **real per-outlet weekly active users (WAU)**, stable per brand across re-entry.

**Non-goals (v1):**
- Per-*brand* real reach (clickstream filtered by `brand_uuid`) — only ~4 aigc-pilot brands have it; deferred to a follow-up.
- Live Databricks query on the onboarding hot path (see §4.2 — snapshot instead).
- SP-QUESTIONS (step 4) and SP-VOICE (step 5) — separate specs; SP-QUESTIONS reuses this spine.

## 3. Key decisions (brainstorm outcomes)

1. **Outlet identities are always real, never LLM-invented.** The universe is the Mlytics publisher-customer catalog. The LLM only *ranks and frames*; it never generates names/hostnames. Server-side enforces `output ⊆ catalog`.
2. **Real catalog source:** Databricks `aigc_prod.reports.member_sheet_registry` — ~15 members (`member_name`, `customer_uuid`, `hostname`).
3. **Per-outlet WAU is real and in v1 scope.** Source: the curated Metric View `aigc_prod.aigc_metrics.aigc_clickstream_metrics`, `MEASURE(unique_visitors)` over the trailing 7 days of available data, grouped by `publisher_name`. Validated magnitudes (2026-05): NOWnews 2.31M, 聯合新聞網 2.01M, 鏡亨網 1.77M, 遠見雜誌 771K, Bella.tw 718K, U-CAR 271K, CMoney 117K, 數位時代 112K, 經理人 75K, 創業小聚 16K, 早安健康 12K. WAU is *per-publisher* (not per-brand), so it exists for the whole catalog at credible scale.
4. **Periodic Databricks → cortex snapshot.** A scheduled cortex-side sync pulls the catalog + latest weekly WAU into a cortex-owned table. The onboarding request path reads only the cortex snapshot — **decoupled from live Databricks** (no dependency on the stopped `cortex-warehouse` / OAuth-M2M creds on the user path; no added latency). WAU "as of last sync" is acceptable because WAU is itself a weekly figure.
5. **LLM matcher, persisted & deterministic.** Reuse the SP-3a async-job + `CORTEX_ANALYZE_*` Claude provider. Result is persisted per brand; re-entry returns the same set; regeneration is explicit.
6. **Mirror SP-3a structure:** new cortex-api domain + async endpoint, web seam swap, projection to the existing `Media` type. No UI redesign.

## 4. Architecture

### 4.1 Databricks (read-only, accessed ONLY by the snapshot sync)

- **Workspace:** `https://dbc-7f36ecbb-68a7.cloud.databricks.com`. Auth via the existing cortex Databricks secret convention (`cortex/<env>/databricks/credentials`, OAuth-M2M). The SQL Statement Execution API or the SQL connector against a SQL warehouse.
- **Metric-View contract:** `aigc_metrics.*` are Databricks **Metric Views** — measure columns require `MEASURE(...)` and only the view's declared dimensions may be grouped. Plain `SELECT col` on a measure errors (`METRIC_VIEW_MISSING_MEASURE_FUNCTION`). Queries:
  - Catalog: `SELECT member_name, customer_uuid, hostname FROM aigc_prod.reports.member_sheet_registry`.
  - WAU: `SELECT publisher_name, MEASURE(unique_visitors) AS wau FROM aigc_prod.aigc_metrics.aigc_clickstream_metrics WHERE event_date >= dateadd(day,-7,(SELECT max(event_date) FROM aigc_prod.aigc_metrics.aigc_clickstream_metrics)) GROUP BY publisher_name`.
- Catalog↔WAU join is on the human publisher name (`member_sheet_registry.member_name` ≈ `aigc_clickstream_metrics.publisher_name`). Names that do not match get `wau = null` (rendered without a number, not dropped).
- **Do not** use raw `aigc_clickstream.events_silver` — dirty timestamps (1970↔2426) and an opaque integer `member_id` with no clean registry join. The curated Metric View already resolved identity + cleaning.

### 4.2 Snapshot sync (cortex-side, scheduled)

- A standalone job (cortex-api management command / scheduled task) queries §4.1 and **upserts** a cortex table `media_network_member`:
  `member_name`, `hostname`, `customer_uuid` (nullable), `wau` (nullable int), `category_hint` (nullable, derived from hostname/name heuristic — informs LLM ranking), `synced_at`.
- Cadence: daily (configurable). Idempotent upsert keyed by `hostname`.
- Bootstrap: an initial seed script (`api/scripts/seed_media_network.sql`) with the validated 15 members + WAU so non-Databricks environments and first boot work without the sync.
- Failure isolation: a failed/unavailable sync leaves the previous snapshot intact and **never breaks onboarding**.

### 4.3 cortex-api domain `service/media_network/`

Mirror the SP-3a domain shape (`container.py`, `config.py`, `service.py`, `repo/`, `model/`, `policy` reuse):
- **Tables (Alembic, async):**
  - `media_network_member` (snapshot, §4.2).
  - `brand_media_network` — `brand_id` (UUID v7 PK, FK→`brand.id`), `outlets` (JSONB: ordered list of `{member_hostname, relevance, why, topics[], context_agent_label, audience_descriptor}`), `status` (ENUM `mediajobstatus`: pending|running|succeeded|failed), `error` (nullable), `created_at`, `updated_at`. Migration rules per `CLAUDE.md` §"Migrations: hard-won rules" (server_default timestamps; `onupdate`; explicit ENUM drop in `downgrade()`; round-trip test).
- **Async job:** reuse the SP-3a `AnalyzeJobService` pattern (in-process worker, dedupe, sweep_stale, cancel_all on shutdown) — generalize or parallel it as `MediaNetworkJobService`.
- **Endpoints** (`app/api/media_network/router.py`, no prefix, full paths):
  - `POST /v1/brand/{brand_id}/media-network` → `202` job accepted (or `200` returning the existing persisted result if present and not regenerating; `?regenerate=true` forces a new job).
  - `GET /v1/brand/{brand_id}/media-network/{job_id}` → job status + result on success.
  - Gates: `Depends(active_brand)` + capability per verb — `POST` requires `BrandCapability.EDIT_BRAND_SETTINGS` (cost-bearing write: triggers an LLM job); `GET` requires `BrandCapability.VIEW_BRAND_DASHBOARD` (read-only poll). Tenant scope strictly from JWT `active_context.id`. _(Updated: @owl review issue 5 — cost-bearing write must not be gated on a read capability.)_

### 4.4 LLM matcher

- Input (server-built, never client-trusted): the persisted `brand_profile` for `brand_id` (name, category, region, products, competitors, about, voice) + the full `media_network_member` snapshot (name, hostname, wau, category_hint).
- Provider: the existing `CORTEX_ANALYZE_*` Claude provider (same config/secret as SP-3a; no new key).
- Output schema (strict JSON): an ordered list of `{member_hostname, relevance:0-100, why:str, topics:str[], context_agent_label:str, audience_descriptor:str}`.
- **Invariant enforcement:** after the LLM returns, the service filters to `member_hostname ∈ snapshot`; any hallucinated/duplicate entry is dropped. If fewer than N remain, backfill deterministically by `category_hint` match then `wau` desc. Final list is truncated to a configured N (default 8, matching current UI).
- Determinism: persist the result in `brand_media_network`; subsequent `POST` without `regenerate` returns the stored result unchanged.

### 4.5 Web

- `web/src/lib/onboarding/http-api.ts`: implement `getMediaNetwork()` (currently modeled) to call new Server Actions `startMediaNetwork()` / `pollMediaNetwork()` (mirror `analyze-actions.ts`), deriving `brandId` + signed `cortex-token` claims from the session server-side.
- Projection → existing `Media` type (`web/src/components/onboarding-v2/data.ts`): `name`←member_name, `id`←hostname, `weeklyReaders`←wau (omit/format when null), `relevance`←relevance, `topics`←topics, `contextAgent`←context_agent_label, `audience`←audience_descriptor, `picked`←top-K default true, `trend`←"flat" (real trend deferred). The step-3 aggregate tiles ("WEEKLY REACH", "CONTEXT AGENTS") derive from the projected list (sum of WAU, count).
- No `step-media.tsx` redesign; only the data source changes (same lesson as SP-3a: the URL-ignoring mock had masked data wiring — add a behavioral test, §7).

## 5. Data flow

1. Background: snapshot sync → `media_network_member` (real names + WAU), daily.
2. User reaches step 3 → web `getMediaNetwork()` → Server Action → `POST /v1/brand/{id}/media-network`.
3. cortex-api: if persisted result exists → return it; else enqueue a job.
4. Job: load `brand_profile` + `media_network_member` snapshot → Claude matcher → enforce `⊆ catalog` invariant → persist `brand_media_network`.
5. Web polls → projects → step 3 renders real ranked outlets + real WAU; tiles aggregate.

## 6. Error handling

- LLM/job failure → SP-3a-style `error` + retry (same UX as analyze).
- Empty/stale snapshot → deterministic fallback: full catalog ranked by `category_hint` match then `wau` desc, no LLM framing (still real names; degrade, don't fail).
- Snapshot sync unavailable / Databricks down → keep prior snapshot; onboarding unaffected.
- Hallucinated outlet names → server-side `⊆ catalog` filter (§4.4); never surfaced.
- Cross-tenant safety: result keyed and read by JWT-derived `brand_id` only (mirror SP-3a tenant tests).

## 7. Testing

- **Unit:** projection mapping; the `⊆ catalog` invariant (LLM output with an injected fake name → filtered out); deterministic backfill ordering; determinism (same brand+snapshot → identical persisted result).
- **Integration:** DI-container override (no `mock.patch`), job lifecycle (pending→running→succeeded/failed), persisted-result short-circuit, cross-tenant isolation.
- **Snapshot sync:** faked Databricks client (DI override) → asserts upsert + failure-isolation (sync error keeps prior rows).
- **Web behavioral:** `render(<StepMedia .../>)` asserts rendered outlet names are a subset of the snapshot and stable across re-render; aggregate tiles equal sum/count of the list.
- Gate parity with SP-3a: `make lint` (ruff/mypy strict, eslint/tsc), `make test`, Alembic round-trip (`upgrade head → downgrade base → upgrade head`).

## 8. Security

- The Databricks token/creds are used **only** by the snapshot sync via the existing `cortex/<env>/databricks/credentials` secret pattern — never on the onboarding request path, never logged. (The PAT shared during brainstorming was for feasibility probing only; production uses the managed secret. Rotate the probing PAT.)
- No secret values in code, logs, or fixtures; seed script carries WAU only (public-ish aggregate), not credentials.

## 9. Scope / decomposition

- This spec is **SP-MEDIA only**. **SP-QUESTIONS** (step 4) is a sibling spec that reuses §4.2 (snapshot infra) + §4.4 (LLM-matcher spine) against `aigc_clickstream_metrics.question_title`. **SP-VOICE** (step 5) is independent (pure LLM, configurable styles) — its own spec.

## 10. Deferred (own follow-ups, not v1)

- Per-*brand* real reach + actually-serving publishers from `aigc_clickstream_metrics` filtered by `brand_uuid` (≈4 aigc-pilot brands today).
- Real week-over-week `trend` per outlet.
- `ai_referral_metrics` cross-source; richer topical taxonomy than `category_hint`.
- Hardening / verifying cortex-api's live Databricks connector + starting `cortex-warehouse` (only needed if v2 moves off the snapshot to live query).

## 11. Decision log

| # | Decision | Rationale |
|---|---|---|
| D1 | Hybrid → in practice LLM-ranks a real catalog | True per-brand real data is ~4 brands; LLM-ranking real names covers all prospects honestly |
| D2 | Names strictly from `member_sheet_registry`, enforced `⊆ catalog` | User requirement: never invented, real network publishers only |
| D3 | Per-outlet WAU real & in v1 (publisher-keyed) | WAU exists for the whole catalog at credible scale; not sparsity-limited like per-brand reach |
| D4 | Periodic snapshot, not live query | Decouples hot path from stopped warehouse / OAuth-creds risk + latency; WAU is weekly anyway |
| D5 | Reuse SP-3a async-job + CORTEX_ANALYZE_* + projection seam | Proven pattern; consistency; no new infra/secret |
| D6 | Persist per brand, deterministic | User requirement: not random per run; stable across re-entry |
