"""Media-network domain DI container."""

from dependency_injector import containers, providers

from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.brand.analyze_config import AnalyzeConfig
from cortex_api.service.brand.analyze_provider import build_provider
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.media_network.config import Config
from cortex_api.service.media_network.job_service import MediaNetworkJobService
from cortex_api.service.media_network.repo.brand_media_repo import BrandMediaRepo
from cortex_api.service.media_network.repo.member_repo import MemberRepo
from cortex_api.service.media_network.snapshot_sync import sync_snapshot


class Container(containers.DeclarativeContainer):
    """DI container for the media-network domain."""

    infra_container = providers.Container(InfraContainer)

    config: providers.Provider[Config] = providers.Singleton(Config)

    database_client = providers.Singleton(infra_container._database_client_factory)
    databricks_client = providers.Singleton(infra_container._databricks_client_factory)

    member_repo: providers.Provider[MemberRepo] = providers.Singleton(MemberRepo)
    brand_media_repo: providers.Provider[BrandMediaRepo] = providers.Singleton(BrandMediaRepo)

    # Shared repo from the Brand bounded context — injected here so the job
    # worker reads brand profile data through the canonical Brand domain repo
    # instead of issuing cross-domain raw SQL (mirrors how AnalyzeJobService
    # injects BrandProfileRepo in service/brand/container.py).
    brand_profile_repo: providers.Provider[BrandProfileRepo] = providers.Singleton(BrandProfileRepo)

    # LLM provider — AnalyzeConfig owns the CORTEX_ANALYZE_* env vars; build_provider
    # constructs the concrete Claude / OpenAI-compat provider from it.
    analyze_config: providers.Provider[AnalyzeConfig] = providers.Singleton(AnalyzeConfig)
    provider = providers.Singleton(build_provider, analyze_config)

    job_service: providers.Provider[MediaNetworkJobService] = providers.Singleton(
        MediaNetworkJobService,
        database_client=database_client,
        brand_media_repo=brand_media_repo,
        member_repo=member_repo,
        config=config,
        brand_profile_repo=brand_profile_repo,
        provider=provider,
    )

    # run_snapshot_sync is a providers.Callable so it is accessible on the
    # DynamicContainer instance (methods defined on the DeclarativeContainer
    # class are NOT forwarded to the DynamicContainer). Calling
    # ``await container.run_snapshot_sync()`` returns the coroutine produced
    # by sync_snapshot, which is then awaitable by the caller.
    run_snapshot_sync = providers.Callable(
        sync_snapshot,
        databricks_client,
        database_client,
        member_repo,
        config.provided.dbx_catalog,
    )
