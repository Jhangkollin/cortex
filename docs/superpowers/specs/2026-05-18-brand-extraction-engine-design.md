# Brand Extraction Engine (`cortex-brand-extract`) — Design

- **Date:** 2026-05-18
- **Status:** Approved (brainstorming) — ready for implementation planning
- **Scope:** SP-2 of the Brand Onboarding program. This spec covers **only** the extraction engine.

## Context

The `/onboarding/v2` brand wizard (`web/src/app/(auth)/onboarding/v2/`) is a
client-only prototype. Its core promise — *paste a URL, we extract your whole
brand* — is faked from seed data (`web/src/components/onboarding-v2/data.ts`).

The program goal has three parts:

1. Make the onboarding flow real and persist collected data.
2. Make the experience reusable so GTM can run it for any prospect brand.
3. End the flow with a shareable Brand Insight one-pager.

This is too large for one spec. We decomposed it into four sub-projects:

| ID | Sub-project | Depends on |
|----|-------------|------------|
| SP-1 | Brand profile write model + persistence (Postgres, tenant-scoped) | — |
| **SP-2** | **Extraction engine — the magic (this spec)** | — |
| SP-3 | Two-mode engine + GTM public surface (auth/persistence boundary) | SP-1 |
| SP-4 | Brand Insight one-pager (shareable artifact) | SP-2, SP-3 |

We build SP-2 first to retire the largest risk — whether real, unattended
extraction is good enough — before investing in persistence, modes, and the
one-pager.

## Locked decisions

1. **One engine, two modes** (program-level): one onboarding engine serves a
   logged-in, persisted product mode and a public, lightweight GTM mode. SP-2
   is mode-agnostic.
2. **Full real extraction**: category, about, brand voice, products,
   competitors, and media-network match — all real, not seeded.
3. **Packaging A — library-first core + MCP façade**: a pure Python package
   `cortex-brand-extract`. cortex-api imports it directly (no production
   network hop) and owns persistence and tenancy (SP-1). An MCP server wraps
   the same functions for GTM and external AI tools. An optional Claude skill
   may drive the MCP tools later.
4. **Tiered fetch, caller-selectable**: a `lite` tier (static fetch, no
   browser, pip-light) and a `deep` tier (headless render for JS-rendered
   SPAs). The caller picks per call.
5. **LLM — pluggable, BYO-key, Claude default**: a provider protocol with a
   Claude adapter (default; prompt caching) and an OpenAI-compatible adapter
   (BytePlus / Databricks-served parity with agent-will-smith). The caller
   supplies provider and key via config or environment.
6. **Pipeline — staged + structured synthesis (Approach A), agentic later**:
   deterministic fetch/crawl/parse produces a normalized corpus; one
   structured-output LLM call synthesizes the profile; competitor and media
   match use deterministic candidates plus an LLM rank. An agentic `deep`
   mode that reuses these stages as tools is a documented future extension.

## Architecture & boundaries

The package takes a URL plus options and returns a `BrandProfile` value
object. It imports nothing from cortex, performs no authentication, and
touches no database.

Three consumers share one core:

- **cortex-api** adds the package as a uv-workspace / path dependency and
  imports `extract_brand_profile`. Persistence and tenant scoping belong to
  cortex-api (SP-1), not the library.
- **`cortex_brand_extract.mcp`** wraps the same functions as MCP tools over
  stdio (and optional HTTP) for GTM and external AI tools.
- An optional **Claude skill** drives the MCP tools for humans in Claude or
  Cursor.

Base install stays pip-light: `httpx`, `selectolax`, `pydantic`, and one
provider adapter. Extras add weight only when needed: `[render]` pulls
Playwright (deep tier); `[mcp]` pulls the MCP server dependencies.

## Package layout

`packages/brand-extract/` is a uv workspace member with its own
`pyproject.toml`. Import name: `cortex_brand_extract`.

```
packages/brand-extract/
  pyproject.toml              # name=cortex-brand-extract; extras: render, mcp
  src/cortex_brand_extract/
    __init__.py               # public API: extract_brand_profile + stage fns + types
    types.py                  # BrandProfile, Product, Competitor, MediaMatch,
                              # VoiceSample, ExtractTier, ProviderConfig (frozen pydantic)
    fetch/
      lite.py                 # httpx + selectolax static fetch
      deep.py                 # Playwright render (import-guarded behind [render])
      detect.py               # JS-rendered heuristic → recommend tier upgrade
    crawl.py                  # bounded link discovery + product-page selection
    parse.py                  # metadata / logo / og / schema.org
    corpus.py                 # token-bounded SiteCorpus assembly
    llm/
      __init__.py             # LLMProvider protocol
      claude.py               # default adapter (prompt caching)
      openai_compat.py        # BytePlus / Databricks-served / OpenAI
    synthesize.py             # one structured-output call: corpus → profile core
    match/
      competitors.py          # deterministic candidates + LLM rank
      media.py                # caller-supplied catalog + LLM rank
    pipeline.py               # orchestrator: stages + progress events
    progress.py               # ProgressEvent model + callback / async-gen
    mcp/
      server.py               # FastMCP: stage tools + extract_brand_profile orchestrator
      __main__.py             # entrypoint: python -m cortex_brand_extract.mcp
  tests/
    fixtures/                 # saved HTML of real prospect sites (offline, deterministic)
    eval/                     # rubric harness + scored runs
```

## Public contract

```python
async def extract_brand_profile(
    url: str,
    *,
    tier: Literal["lite", "deep"] = "lite",
    provider: ProviderConfig,
    max_pages: int = 12,
    seed_media_catalog: list[MediaOutlet] | None = None,
    progress: ProgressSink | None = None,
) -> BrandProfile: ...
```

The stage functions are also public, so MCP tools and tests call them
granularly: `fetch_site`, `crawl_pages`, `parse_site`, `build_corpus`,
`synthesize_profile`, `match_competitors`, `match_media`.

`BrandProfile` is a **frozen Pydantic value object**, not SQLModel. This
respects cortex's read/write split and keeps the library cortex-agnostic. Its
fields align with the web `ExtractedBrand` TypeScript type
(`web/src/components/onboarding-v2/data.ts`) **where the data overlaps** — it
is the extraction read model, not a wire-format for the wizard. It is
deliberately **not** a 1:1 passthrough: UI-only fields (`id`, `picked`,
`icon`), camelCase casing, non-optional-string coercion, and derived counts
like `productMoreCount` are **not** the library's concern. Mapping
`BrandProfile` → `ExtractedBrand` (snake→camel, null-coalescing, UI-field
synthesis, `productMoreCount` derivation) is owned by the **SP-3 projection
layer** (`HttpOnboardingApi.analyzeBrand`), not by this library and not by the
wizard. `BrandProfile` adds an `extraction_meta` block:
`{tier, model, cost, js_detected, warnings[]}` (`model` is the resolved model
identifier actually used, e.g. `claude-opus-4-7`).

SP-1 later maps the persistable subset of `BrandProfile` onto the existing
`brand_profile` SQLModel (`api/src/cortex_api/service/brand/model/profile.py`)
plus child tables. The library does not own that mapping.

BYO-key: `ProviderConfig(kind, api_key, model, base_url?)` is read from
environment or tool arguments, so external callers bring their own LLM
credentials.

## Pipeline & data flow (Approach A)

```
fetch homepage
  → parse metadata / logo / og / schema.org
  → discover & select pages (bounded ≤ max_pages)
  → crawl pages (tier-aware: lite static / deep render)
  → assemble token-bounded SiteCorpus
  → ONE structured-output LLM synthesis (category · about · voice · products)
  → competitor match (deterministic candidates + LLM rank)
  → media match (caller seed_media_catalog + LLM rank)
  → done
```

Each stage is a pure async function that emits a `ProgressEvent`. The events
follow the same narrative arc as the wizard's `StepCrawl` tasks and can drive
that progress UI; the exact event-to-task mapping is settled when the wizard
is wired (SP-1 / SP-3) and is out of scope here. Progress is delivered by an
async generator or callback; the MCP server maps it to MCP progress
notifications. The synthesis system prompt is prompt-cached, so re-runs stay
cheap.

## Error handling & degradation

- **Honest degradation, never silent garbage.** A JS-render heuristic detects
  low text/DOM density, sets `js_detected=true`, emits a warning, and
  recommends the `deep` tier.
- **Per-stage isolation.** A failed product-page fetch degrades that one
  product, not the run. The pipeline returns a partial `BrandProfile` with
  populated `warnings[]`.
- **Typed upstream errors.** LLM and fetch failures raise `UpstreamError` /
  `UpstreamTimeoutError`, mirroring agent-will-smith. Bounded retries with
  backoff. Invalid structured output triggers one repair retry, then a typed
  error.
- **Cost is bounded and recorded.** `max_pages`, a corpus token cap, and a
  single synthesis call keep spend predictable; `extraction_meta.cost`
  records it.
- **Politeness.** Respect `robots.txt`, cap concurrency, set a per-request
  timeout, and send an identifying user-agent.

## Testing & spike definition-of-done

**Tests.** Offline and deterministic: saved real-site HTML fixtures drive
stage unit tests with no network or LLM (the provider protocol is faked via
injection). A stub provider checks structured-output schema conformance.

**Eval harness.** Six to eight real prospect URLs across verticals, including
at least one JS-rendered SPA and at least one real bank. Each run produces a
`BrandProfile` scored by a human on a 1–5 rubric per facet.

**The spike is done when:**

- the library imports cleanly and the MCP server is callable from Claude and
  the `mcp` CLI;
- the median rubric score is ≥ 4 for category, about, and products, and ≥ 3
  for voice;
- the `deep` tier scores ≥ the `lite` tier on JS-rendered sites;
- cost stays under target — roughly ≤ $0.10 (lite) and ≤ $0.30 (deep) per
  extraction with prompt caching.

## Out of scope (deferred to other specs)

- cortex-api wiring, DI container, router — SP-1 / SP-3.
- Persistence, migrations, tenant scoping — SP-1.
- Auth, GTM public link, mode boundary — SP-3.
- The Brand Insight one-pager — SP-4.
- Agentic `deep` extraction (Approach B) — future extension; the stage tools
  are designed to become its toolset.

## Risks & open questions

- **Competitor candidate source.** Deterministic candidate generation needs a
  source (search, the seed list, or a small curated set). The implementation
  plan must pick one; the LLM only ranks candidates, it does not invent them.
- **Media catalog ownership.** `seed_media_catalog` is caller-supplied for the
  spike. Where the real catalog lives (Library context vs. Databricks) is an
  SP-4 / Library question.
- **uv workspace wiring.** cortex-api currently builds from `api/` alone. The
  plan must confirm the workspace/path-dependency mechanics so cortex-api can
  import the package without publishing it.
- **Deep-tier deploy weight.** Playwright/Chromium in the hosted MCP image is
  heavy; the hosted profile must opt into `[render]` deliberately.

## Key references

- Wizard prototype: `web/src/app/(auth)/onboarding/v2/page.tsx`
- Faked extraction data + `ExtractedBrand` type: `web/src/components/onboarding-v2/data.ts`
- Persistence target (SP-1): `api/src/cortex_api/service/brand/model/profile.py`
- DI / convention source: `../agent-will-smith` (`infra/llm_client.py` pattern)
- Fetcher pattern to crib: `../aigc-mvp/scripts/geo-placement/generate_infographic.py`
