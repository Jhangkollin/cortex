"""Identity (shared user) domain config."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Shared identity config — AppUser / OAuth recognition only.

    Brand/publisher-specific config lives in their respective domains.
    """

    model_config = SettingsConfigDict(env_prefix="CORTEX_IDENTITY_", extra="forbid")
