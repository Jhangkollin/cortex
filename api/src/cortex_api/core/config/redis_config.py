"""Redis cache config."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisConfig(BaseSettings):
    """ElastiCache Redis connection config."""

    model_config = SettingsConfigDict(env_prefix="CORE_REDIS_", extra="forbid")

    url: str = Field(default="redis://localhost:6379/0")
    default_ttl: int = Field(default=300, description="Default cache TTL in seconds (5 min)")
