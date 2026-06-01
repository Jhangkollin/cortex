"""Brand (write-side) domain config."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Brand profile service config."""

    model_config = SettingsConfigDict(env_prefix="CORTEX_BRAND_", extra="forbid")
