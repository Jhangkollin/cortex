"""Brand report domain DI container."""

from dependency_injector import containers, providers

from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.brand.analyze_config import AnalyzeConfig
from cortex_api.service.brand.analyze_provider import build_provider
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.brand_report.config import Config
from cortex_api.service.brand_report.job_service import BrandReportJobService
from cortex_api.service.brand_report.pdf.renderer import render_pdf
from cortex_api.service.brand_report.pdf_service import BrandReportPdfService
from cortex_api.service.brand_report.repo.report_repo import BrandReportRepo
from cortex_api.service.brand_report.repo.ui_state_repo import ReportUiStateRepo
from cortex_api.service.brand_report.service import BrandReportService
from cortex_api.service.brand_report.ui_state_service import BrandReportUiStateService
from cortex_api.service.media_network.repo.brand_media_repo import BrandMediaRepo
from cortex_api.service.questions.repo.brand_questions_repo import BrandQuestionsRepo


class Container(containers.DeclarativeContainer):
    """DI container for the brand report domain."""

    infra_container = providers.Container(InfraContainer)

    config: providers.Provider[Config] = providers.Singleton(Config)

    database_client = providers.Singleton(infra_container._database_client_factory)

    report_repo: providers.Provider[BrandReportRepo] = providers.Singleton(BrandReportRepo)
    profile_repo: providers.Provider[BrandProfileRepo] = providers.Singleton(BrandProfileRepo)
    media_repo: providers.Provider[BrandMediaRepo] = providers.Singleton(BrandMediaRepo)
    questions_repo: providers.Provider[BrandQuestionsRepo] = providers.Singleton(BrandQuestionsRepo)
    ui_state_repo: providers.Provider[ReportUiStateRepo] = providers.Singleton(ReportUiStateRepo)

    # LLM provider — AnalyzeConfig owns the CORTEX_ANALYZE_* env vars; build_provider
    # constructs the concrete Claude / OpenAI-compat provider from it.
    analyze_config: providers.Provider[AnalyzeConfig] = providers.Singleton(AnalyzeConfig)
    provider = providers.Singleton(build_provider, analyze_config)

    service: providers.Provider[BrandReportService] = providers.Singleton(
        BrandReportService,
        database_client=database_client,
        report_repo=report_repo,
    )
    job_service: providers.Provider[BrandReportJobService] = providers.Singleton(
        BrandReportJobService,
        database_client=database_client,
        report_repo=report_repo,
        profile_repo=profile_repo,
        media_repo=media_repo,
        questions_repo=questions_repo,
        provider=provider,
        config=config,
    )

    ui_state_service: providers.Provider[BrandReportUiStateService] = providers.Singleton(
        BrandReportUiStateService,
        database_client=database_client,
        ui_state_repo=ui_state_repo,
        report_repo=report_repo,
    )

    # The bare render_pdf coroutine-function is injected directly; pdf_service
    # passes timeout/concurrency from config at call time. Tests override this
    # provider with a fake via container.renderer.override(...).
    renderer = providers.Object(render_pdf)

    pdf_service: providers.Provider[BrandReportPdfService] = providers.Singleton(
        BrandReportPdfService,
        service=service,
        renderer=renderer,
        config=config,
    )
