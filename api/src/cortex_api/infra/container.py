"""Infra container — factory providers for external clients.

Per-service containers reference these factories; this container does not
contain business logic. References CoreContainer for config.
"""

from dependency_injector import containers, providers

from cortex_api.core.container import Container as CoreContainer
from cortex_api.infra.database_client import DatabaseClient
from cortex_api.infra.databricks_client import DatabricksClient
from cortex_api.infra.redis_client import RedisClient
from cortex_api.infra.vector_search_client import VectorSearchClient


class Container(containers.DeclarativeContainer):
    """Infrastructure clients."""

    core_container = providers.Container(CoreContainer)

    # --- Database (AWS RDS PostgreSQL) --------------------------------------
    _database_client_factory = providers.Singleton(
        DatabaseClient,
        url=core_container.database_config.provided.url,
        pool_size=core_container.database_config.provided.pool_size,
        pool_pre_ping=core_container.database_config.provided.pool_pre_ping,
        echo=core_container.database_config.provided.echo,
    )

    # --- Redis (ElastiCache) -------------------------------------------------
    _redis_client_factory = providers.Singleton(
        RedisClient,
        url=core_container.redis_config.provided.url,
        default_ttl=core_container.redis_config.provided.default_ttl,
    )

    # --- Databricks SQL Warehouse --------------------------------------------
    _databricks_client_factory = providers.Singleton(
        DatabricksClient,
        host=core_container.databricks_config.provided.host,
        http_path=core_container.databricks_config.provided.http_path,
        client_id=core_container.databricks_config.provided.client_id,
        client_secret=core_container.databricks_config.provided.client_secret,
        query_timeout_seconds=core_container.databricks_config.provided.query_timeout_seconds,
    )

    # --- Databricks Vector Search --------------------------------------------
    _vector_search_client_factory = providers.Singleton(
        VectorSearchClient,
        endpoint=core_container.vector_search_config.provided.endpoint,
        index=core_container.vector_search_config.provided.index,
    )
