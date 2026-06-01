"""Databricks SQL Warehouse config — service-principal OAuth."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabricksConfig(BaseSettings):
    """Databricks SQL Warehouse connection config."""

    model_config = SettingsConfigDict(env_prefix="CORE_DATABRICKS_", extra="forbid")

    host: str = Field(default="", description="Workspace hostname")
    http_path: str = Field(default="", description="SQL Warehouse HTTP path")
    client_id: str = Field(default="", description="Service principal client ID (UUID)")
    client_secret: str = Field(default="", description="Service principal secret")
    query_timeout_seconds: int = Field(default=30)
