"""Identity (shared user) domain DI container."""

from dependency_injector import containers, providers

from cortex_api.core.container import Container as CoreContainer
from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.identity.config import Config
from cortex_api.service.identity.repo.user_repo import UserRepo
from cortex_api.service.identity.service import UserService


class Container(containers.DeclarativeContainer):
    """DI container for the shared identity domain (AppUser + OAuth)."""

    core_container = providers.Container(CoreContainer)
    infra_container = providers.Container(InfraContainer)

    config: providers.Provider[Config] = providers.Singleton(Config)

    database_client = providers.Singleton(infra_container._database_client_factory)

    user_repo: providers.Provider[UserRepo] = providers.Singleton(UserRepo)

    service: providers.Provider[UserService] = providers.Singleton(
        UserService,
        database_client=database_client,
        user_repo=user_repo,
        config=config,
    )
