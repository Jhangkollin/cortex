"""FastAPI app config."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FastAPIConfig(BaseSettings):
    """FastAPI runtime config."""

    model_config = SettingsConfigDict(env_prefix="CORE_FASTAPI_", extra="forbid")

    port: int = Field(default=8000)
    debug: bool = Field(default=False)
    title: str = Field(default="Cortex API")
    # Field name matches chart key (CORE_FASTAPI_APP_VERSION) — image SHA is
    # the deployment unit, so app_version tracks it.
    app_version: str = Field(default="0.1.0")
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    docs_url: str | None = Field(default="/docs")
    openapi_url: str = Field(default="/openapi.json")
