"""Databricks Vector Search config."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class VectorSearchConfig(BaseSettings):
    """Databricks Vector Search endpoint config."""

    model_config = SettingsConfigDict(env_prefix="CORE_VECTOR_SEARCH_", extra="forbid")

    endpoint: str = Field(default="", description="Vector Search endpoint name")
    index: str = Field(default="", description="Default index name")
