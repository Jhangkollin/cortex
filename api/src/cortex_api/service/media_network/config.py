# api/src/cortex_api/service/media_network/config.py
"""Media-network domain config."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Media-network service config."""

    model_config = SettingsConfigDict(env_prefix="CORTEX_MEDIA_", extra="forbid")

    outlet_count: int = 8
    stale_job_seconds: int = 180
    dbx_catalog: str = "aigc_prod"
