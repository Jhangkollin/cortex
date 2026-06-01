"""Core container — singleton configuration providers.

Mirrors agent-will-smith's pattern: this container owns Pydantic BaseSettings
instances and nothing else. Infra clients live in InfraContainer; business
logic lives in per-service containers.
"""

from dependency_injector import containers, providers

from cortex_api.core.config.auth_config import AuthConfig
from cortex_api.core.config.database_config import DatabaseConfig
from cortex_api.core.config.databricks_config import DatabricksConfig
from cortex_api.core.config.fastapi_config import FastAPIConfig
from cortex_api.core.config.log_config import LogConfig
from cortex_api.core.config.redis_config import RedisConfig
from cortex_api.core.config.service_token_config import ServiceTokenConfig
from cortex_api.core.config.vector_search_config import VectorSearchConfig


class Container(containers.DeclarativeContainer):
    """Core infrastructure container providing global configuration."""

    auth_config = providers.Singleton(AuthConfig)
    database_config = providers.Singleton(DatabaseConfig)
    databricks_config = providers.Singleton(DatabricksConfig)
    fastapi_config = providers.Singleton(FastAPIConfig)
    log_config = providers.Singleton(LogConfig)
    redis_config = providers.Singleton(RedisConfig)
    service_token_config = providers.Singleton(ServiceTokenConfig)
    vector_search_config = providers.Singleton(VectorSearchConfig)
