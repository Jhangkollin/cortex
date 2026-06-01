"""Publisher identity domain DI container."""

from dependency_injector import containers, providers

from cortex_api.core.container import Container as CoreContainer
from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.publisher_identity.config import Config
from cortex_api.service.publisher_identity.repo.publisher_membership_repo import PublisherMembershipRepo
from cortex_api.service.publisher_identity.repo.publisher_repo import PublisherRepo
from cortex_api.service.publisher_identity.service import PublisherIdentityService


class Container(containers.DeclarativeContainer):
    """DI container for the publisher identity domain."""

    core_container = providers.Container(CoreContainer)
    infra_container = providers.Container(InfraContainer)

    config: providers.Provider[Config] = providers.Singleton(Config)

    database_client = providers.Singleton(infra_container._database_client_factory)

    publisher_repo: providers.Provider[PublisherRepo] = providers.Singleton(
        PublisherRepo, database_client=database_client
    )
    membership_repo: providers.Provider[PublisherMembershipRepo] = providers.Singleton(
        PublisherMembershipRepo, database_client=database_client
    )

    service: providers.Provider[PublisherIdentityService] = providers.Singleton(
        PublisherIdentityService,
        publisher_repo=publisher_repo,
        membership_repo=membership_repo,
        config=config,
    )
