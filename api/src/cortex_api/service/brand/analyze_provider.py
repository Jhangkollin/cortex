"""Build a cortex_brand_extract LLMProvider from AnalyzeConfig."""

from __future__ import annotations

from cortex_brand_extract.llm.claude import ClaudeProvider
from cortex_brand_extract.llm.openai_compat import OpenAICompatProvider
from cortex_brand_extract.types import ProviderConfig

from cortex_api.service.brand.analyze_config import AnalyzeConfig


def build_provider(config: AnalyzeConfig) -> ClaudeProvider | OpenAICompatProvider:
    """Construct the SP-2 provider. OpenAI-compat requires base_url."""
    cfg = ProviderConfig(
        kind=config.provider_kind,
        api_key=config.api_key,
        model=config.model,
        base_url=config.base_url,
    )
    if config.provider_kind == "openai_compat":
        if not config.base_url:
            raise ValueError("openai_compat provider requires base_url")
        return OpenAICompatProvider(cfg)
    return ClaudeProvider(cfg)
