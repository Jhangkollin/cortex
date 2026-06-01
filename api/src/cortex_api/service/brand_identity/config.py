"""Brand identity domain config."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Brand identity service config."""

    model_config = SettingsConfigDict(env_prefix="CORTEX_BRAND_IDENTITY_", extra="forbid")
