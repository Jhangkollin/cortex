"""Publisher identity domain config."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Publisher identity service config."""

    model_config = SettingsConfigDict(env_prefix="CORTEX_PUBLISHER_IDENTITY_", extra="forbid")
