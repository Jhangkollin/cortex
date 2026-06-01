# cortex-brand-extract

URL → structured `BrandProfile`. Pure library (no auth, no DB). Used by
cortex-api directly and exposed to AI tools via an MCP server.

## Install

```bash
pip install cortex-brand-extract                 # lite tier only
pip install 'cortex-brand-extract[render]'       # + deep (Playwright) tier
pip install 'cortex-brand-extract[mcp]'          # + MCP server
playwright install chromium                      # once, for the deep tier
```

## Library use

```python
import asyncio
from cortex_brand_extract import extract_brand_profile
from cortex_brand_extract.llm.claude import ClaudeProvider
from cortex_brand_extract.types import ProviderConfig

provider = ClaudeProvider(
    ProviderConfig(kind="claude", api_key="sk-...", model="claude-sonnet-4-6")
)
profile = asyncio.run(extract_brand_profile("acmebank.asia", tier="lite", provider=provider))
print(profile.model_dump_json(indent=2))
```

## MCP server (BYO-key)

```bash
CORTEX_EXTRACT_API_KEY=sk-... python -m cortex_brand_extract.mcp
```

Tools: `extract_brand_profile`, `fetch_site`. Pass `provider_kind`,
`model`, and `api_key` per call, or set `CORTEX_EXTRACT_API_KEY`.

## Tiers

- `lite` — static fetch, no browser, pip-light.
- `deep` — headless render for JS-heavy SPA sites (needs `[render]`).

## Output contract (important for consumers)

`BrandProfile` is the **extraction read model**, not the wizard wire-format.
It is snake_case, has nullable strings, and intentionally omits UI-only
fields (`id`, `picked`, `icon`) and derived counts (`productMoreCount`).
A consumer that needs the web `ExtractedBrand` shape (e.g. the SP-3
`HttpOnboardingApi`) owns the projection: snake→camel casing,
null-coalescing, UI-field synthesis, `productMoreCount` derivation.
`extraction_meta.model` is the resolved model id actually used.

## Scope

This is SP-2 of the brand onboarding program. Persistence, GTM mode, and
the one-pager live in cortex-api / SP-1 / SP-3 / SP-4. Known SP-3 wiring
follow-ups: `HttpOnboardingApi` projection (above); the onboarding wizard's
`restart()` currently re-analyzes a hardcoded URL instead of the user's —
fix when the real adapter is wired.
