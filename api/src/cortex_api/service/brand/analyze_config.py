"""Analyze-pipeline config (server-managed SP-2 LLM key + job tuning)."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class AnalyzeConfig(BaseSettings):
    """SP-2 provider + analyze-job settings. Key is server-managed (Secrets)."""

    model_config = SettingsConfigDict(env_prefix="CORTEX_ANALYZE_", extra="forbid")

    provider_kind: Literal["claude", "openai_compat"] = "claude"
    api_key: str = ""
    model: str = "claude-opus-4-7"
    base_url: str | None = None
    tier: str = "lite"
    stale_job_seconds: int = 900
