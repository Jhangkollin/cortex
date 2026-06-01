"""Voice domain DI container."""

from dependency_injector import containers, providers

from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.brand.analyze_config import AnalyzeConfig
from cortex_api.service.brand.analyze_provider import build_provider
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.voice.config import Config
from cortex_api.service.voice.job_service import VoiceJobService
from cortex_api.service.voice.repo.brand_voice_repo import BrandVoiceRepo


class Container(containers.DeclarativeContainer):
    """DI container for the voice domain."""

    infra_container = providers.Container(InfraContainer)

    config: providers.Provider[Config] = providers.Singleton(Config)

    database_client = providers.Singleton(infra_container._database_client_factory)

    brand_voice_repo: providers.Provider[BrandVoiceRepo] = providers.Singleton(BrandVoiceRepo)

    # Shared repo from the Brand bounded context — injected here so the job
    # worker reads brand profile data through the canonical Brand domain repo
    # instead of issuing cross-domain raw SQL (mirrors how MediaNetworkJobService
    # injects BrandProfileRepo in service/media_network/container.py).
    brand_profile_repo: providers.Provider[BrandProfileRepo] = providers.Singleton(BrandProfileRepo)

    # LLM provider — AnalyzeConfig owns the CORTEX_ANALYZE_* env vars; build_provider
    # constructs the concrete Claude / OpenAI-compat provider from it.
    analyze_config: providers.Provider[AnalyzeConfig] = providers.Singleton(AnalyzeConfig)
    provider = providers.Singleton(build_provider, analyze_config)

    job_service: providers.Provider[VoiceJobService] = providers.Singleton(
        VoiceJobService,
        database_client=database_client,
        brand_voice_repo=brand_voice_repo,
        config=config,
        brand_profile_repo=brand_profile_repo,
        provider=provider,
    )
