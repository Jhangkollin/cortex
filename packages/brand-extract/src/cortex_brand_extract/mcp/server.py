"""FastMCP server. BYO-key: callers pass provider kind/key/model as tool
arguments (or set CORTEX_EXTRACT_API_KEY in the server env).
"""

from __future__ import annotations

import os
from typing import Any, cast

from mcp.server.fastmcp import FastMCP

from cortex_brand_extract.fetch.lite import fetch_lite
from cortex_brand_extract.llm.claude import ClaudeProvider
from cortex_brand_extract.llm.openai_compat import OpenAICompatProvider
from cortex_brand_extract.pipeline import extract_brand_profile as _extract_brand_profile
from cortex_brand_extract.types import ExtractTier, ProviderConfig, ProviderKind


def _provider(
    kind: ProviderKind, model: str, api_key: str | None, base_url: str | None
) -> ClaudeProvider | OpenAICompatProvider:
    key = api_key or os.environ.get("CORTEX_EXTRACT_API_KEY", "")
    cfg = ProviderConfig(kind=kind, api_key=key, model=model, base_url=base_url)
    return ClaudeProvider(cfg) if kind == "claude" else OpenAICompatProvider(cfg)


def build_server() -> FastMCP:
    mcp = FastMCP("cortex-brand-extract")

    @mcp.tool()
    async def fetch_site(url: str) -> dict[str, Any]:
        """Fetch a single page (lite/static). Returns status + html length."""
        page = await fetch_lite(url)
        return {"final_url": page.final_url, "status": page.status, "chars": len(page.html)}

    @mcp.tool()
    async def extract_brand_profile(
        url: str,
        tier: str = "lite",
        provider_kind: str = "claude",
        # Default downgraded from claude-opus-4-7 to claude-sonnet-4-6 for cost.
        # The lite-tier corpus (~60k chars) on Opus came in ~6× the $0.10 spike
        # target without prompt-cache benefit; Sonnet 4.6 reduces per-call cost
        # by roughly 5× at comparable extraction quality for this surface. Flip
        # back to Opus per call by passing `model="claude-opus-4-7"`.
        model: str = "claude-sonnet-4-6",
        api_key: str | None = None,
        base_url: str | None = None,
        max_pages: int = 12,
    ) -> dict[str, Any]:
        """Extract a full BrandProfile from a brand URL."""
        prov = _provider(cast(ProviderKind, provider_kind), model, api_key, base_url)
        profile = await _extract_brand_profile(
            url,
            tier=cast(ExtractTier, tier),
            provider=prov,
            max_pages=max_pages,
        )
        return profile.model_dump(mode="json")

    return mcp
