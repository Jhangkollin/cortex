"""Logging config."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogConfig(BaseSettings):
    """structlog config."""

    model_config = SettingsConfigDict(env_prefix="CORE_LOG_", extra="forbid")

    level: str = Field(default="INFO")
    format: str = Field(default="json", description="'json' for prod, 'console' for dev")
