# api/src/cortex_api/service/voice/config.py
"""Voice domain config."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Brand-voice service config."""

    model_config = SettingsConfigDict(env_prefix="CORTEX_VOICE_", extra="forbid")

    stale_job_seconds: int = 180
