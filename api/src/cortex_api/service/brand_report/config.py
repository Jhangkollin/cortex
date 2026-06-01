from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CORTEX_BRAND_REPORT_", extra="forbid")
    estimated_seconds: int = 8
    stale_job_seconds: int = 900
    page_count: int = 8
    prepared_by: str = "Cortex · Brand Agent"
    pdf_render_timeout_ms: int = 15_000
    pdf_max_concurrent_renders: int = 2
