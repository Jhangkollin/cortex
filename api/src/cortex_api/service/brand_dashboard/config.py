"""Brand Dashboard projection config."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Brand Dashboard projection config."""

    model_config = SettingsConfigDict(env_prefix="CORTEX_BRAND_DASHBOARD_", extra="ignore")

    cache_ttl_seconds: int = 300
    gold_metrics_table: str = "aigc_metrics.gold_brand_answer_metrics"
    gold_publisher_table: str = "aigc_metrics.gold_brand_publisher_breakdown"
    publisher_page_default_limit: int = 20
