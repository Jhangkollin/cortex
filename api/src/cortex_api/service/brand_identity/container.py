"""Brand identity domain DI container."""

from dependency_injector import containers, providers

from cortex_api.core.container import Container as CoreContainer
from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.brand_identity.config import Config
from cortex_api.service.brand_identity.repo.brand_membership_repo import BrandMembershipRepo
from cortex_api.service.brand_identity.repo.brand_repo import BrandRepo
from cortex_api.service.brand_identity.service import BrandIdentityService


class Container(containers.DeclarativeContainer):
    """DI container for the brand identity domain."""

    core_container = providers.Container(CoreContainer)
    infra_container = providers.Container(InfraContainer)

    config: providers.Provider[Config] = providers.Singleton(Config)

    database_client = providers.Singleton(infra_container._database_client_factory)

    brand_repo: providers.Provider[BrandRepo] = providers.Singleton(BrandRepo)
    membership_repo: providers.Provider[BrandMembershipRepo] = providers.Singleton(BrandMembershipRepo)

    service: providers.Provider[BrandIdentityService] = providers.Singleton(
        BrandIdentityService,
        database_client=database_client,
        brand_repo=brand_repo,
        membership_repo=membership_repo,
        config=config,
    )
