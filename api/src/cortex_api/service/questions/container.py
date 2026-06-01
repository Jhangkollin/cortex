"""Questions domain DI container."""

from dependency_injector import containers, providers

from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.brand.analyze_config import AnalyzeConfig
from cortex_api.service.brand.analyze_provider import build_provider
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.questions.config import Config
from cortex_api.service.questions.job_service import QuestionsJobService
from cortex_api.service.questions.repo.brand_questions_repo import BrandQuestionsRepo
from cortex_api.service.questions.repo.question_repo import QuestionRepo
from cortex_api.service.questions.snapshot_sync import sync_snapshot


class Container(containers.DeclarativeContainer):
    """DI container for the questions domain."""

    infra_container = providers.Container(InfraContainer)

    config: providers.Provider[Config] = providers.Singleton(Config)

    database_client = providers.Singleton(infra_container._database_client_factory)
    databricks_client = providers.Singleton(infra_container._databricks_client_factory)

    question_repo: providers.Provider[QuestionRepo] = providers.Singleton(QuestionRepo)
    brand_questions_repo: providers.Provider[BrandQuestionsRepo] = providers.Singleton(BrandQuestionsRepo)

    # Shared repo from the Brand bounded context — injected here so the job
    # worker reads brand profile data through the canonical Brand domain repo
    # instead of issuing cross-domain raw SQL (mirrors how AnalyzeJobService
    # injects BrandProfileRepo in service/brand/container.py).
    brand_profile_repo: providers.Provider[BrandProfileRepo] = providers.Singleton(BrandProfileRepo)

    # LLM provider — AnalyzeConfig owns the CORTEX_ANALYZE_* env vars; build_provider
    # constructs the concrete Claude / OpenAI-compat provider from it.
    analyze_config: providers.Provider[AnalyzeConfig] = providers.Singleton(AnalyzeConfig)
    provider = providers.Singleton(build_provider, analyze_config)

    job_service: providers.Provider[QuestionsJobService] = providers.Singleton(
        QuestionsJobService,
        database_client=database_client,
        brand_questions_repo=brand_questions_repo,
        question_repo=question_repo,
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
        question_repo,
        config.provided.dbx_catalog,
    )
