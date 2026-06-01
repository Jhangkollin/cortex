"""Brand Dashboard projection DI container."""

from dependency_injector import containers, providers

from cortex_api.core.container import Container as CoreContainer
from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.brand_dashboard.config import Config
from cortex_api.service.brand_dashboard.repo.brand_metrics_repo import BrandMetricsRepo
from cortex_api.service.brand_dashboard.service import BrandDashboardService


class Container(containers.DeclarativeContainer):
    """DI container for the Brand Dashboard projection."""

    core_container = providers.Container(CoreContainer)
    infra_container = providers.Container(InfraContainer)

    config: providers.Provider[Config] = providers.Singleton(Config)

    databricks_client = providers.Singleton(infra_container._databricks_client_factory)
    redis_client = providers.Singleton(infra_container._redis_client_factory)

    repo: providers.Provider[BrandMetricsRepo] = providers.Singleton(
        BrandMetricsRepo,
        databricks_client=databricks_client,
        config=config,
    )

    service: providers.Provider[BrandDashboardService] = providers.Singleton(
        BrandDashboardService,
        repo=repo,
        redis_client=redis_client,
        config=config,
    )
