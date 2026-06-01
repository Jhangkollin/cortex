"""Brand (write-side) domain DI container."""

from dependency_injector import containers, providers

from cortex_api.core.background import BackgroundTaskTracker
from cortex_api.core.container import Container as CoreContainer
from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.brand.analyze_config import AnalyzeConfig
from cortex_api.service.brand.analyze_service import AnalyzeJobService
from cortex_api.service.brand.config import Config
from cortex_api.service.brand.repo.analysis_job_repo import AnalysisJobRepo
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.brand.service import BrandService
from cortex_api.service.placement.cache.eligible_brands_cache import EligibleBrandsCache
from cortex_api.service.placement.composer import BrandPlacementComposer
from cortex_api.service.placement.placement_claim_config import PlacementClaimConfig
from cortex_api.service.placement.repo.eligible_brands_repo import EligibleBrandsRepo
from cortex_api.service.placement.repo.placement_claim_repo import PlacementClaimRepo
from cortex_api.service.placement.repo.settings_repo import PlacementSettingsRepo
from cortex_api.service.placement.service.eligible_brands_service import EligibleBrandsService
from cortex_api.service.placement.service.placement_claim_service import (
    PlacementClaimService,
)


class Container(containers.DeclarativeContainer):
    """DI container for the brand profile domain.

    Placement-owned singletons (``tracker`` and ``settings_repo``) are
    declared here as ``providers.Dependency``: they have no default and
    must be supplied by the composition root (``main.py``). This makes
    the cross-domain seam explicit — instantiating ``Container()`` without
    wiring those two raises ``DependencyError`` immediately, instead of
    silently getting a second tracker that the lifespan-shutdown drain
    would never visit. Reviewer feedback (PR #52 Issue 4): the previous
    ``providers.Container(PlacementContainer)`` + ``override(...)``
    pattern hid the wiring inside ``main.py`` and let test fixtures
    diverge from production.
    """

    core_container = providers.Container(CoreContainer)
    infra_container = providers.Container(InfraContainer)

    # Placement-owned singletons — wired explicitly by main.py from the
    # process-wide PlacementContainer instance.
    tracker: providers.Provider[BackgroundTaskTracker] = providers.Dependency()
    settings_repo: providers.Provider[PlacementSettingsRepo] = providers.Dependency()

    # Cache + repos for eligible-brands (wired by main.py, no defaults).
    eligible_brands_cache: providers.Provider[EligibleBrandsCache] = providers.Dependency()
    eligible_brands_repo: providers.Provider[EligibleBrandsRepo] = providers.Dependency()

    config: providers.Provider[Config] = providers.Singleton(Config)

    database_client = providers.Singleton(infra_container._database_client_factory)

    profile_repo: providers.Provider[BrandProfileRepo] = providers.Singleton(BrandProfileRepo)

    # Composer is provided here because its constructor needs
    # ``BrandProfileRepo`` (brand-owned). The class itself lives at
    # ``service/placement/composer.py`` — see that module's header for
    # the rationale on why DI home and class home differ.
    composer: providers.Provider[BrandPlacementComposer] = providers.Singleton(
        BrandPlacementComposer,
        database_client=database_client,
        profile_repo=profile_repo,
        settings_repo=settings_repo,
        cache=eligible_brands_cache,
    )

    eligible_brands_service: providers.Provider[EligibleBrandsService] = providers.Singleton(
        EligibleBrandsService,
        database_client=database_client,
        repo=eligible_brands_repo,
        cache=eligible_brands_cache,
    )

    # F2b — placement-claims (COR-75 / AD8).
    placement_claim_config: providers.Provider[PlacementClaimConfig] = providers.Singleton(PlacementClaimConfig)
    placement_claim_repo: providers.Provider[PlacementClaimRepo] = providers.Singleton(PlacementClaimRepo)

    placement_claim_service: providers.Provider[PlacementClaimService] = providers.Singleton(
        PlacementClaimService,
        database_client=database_client,
        repo=placement_claim_repo,
        eligible_brands_service=eligible_brands_service,
        config=placement_claim_config,
    )

    service: providers.Provider[BrandService] = providers.Singleton(
        BrandService,
        database_client=database_client,
        profile_repo=profile_repo,
        config=config,
        composer=composer,
        tracker=tracker,
    )

    analyze_config: providers.Provider[AnalyzeConfig] = providers.Singleton(AnalyzeConfig)

    analysis_job_repo: providers.Provider[AnalysisJobRepo] = providers.Singleton(AnalysisJobRepo)

    analyze_service: providers.Provider[AnalyzeJobService] = providers.Singleton(
        AnalyzeJobService,
        database_client=database_client,
        analysis_job_repo=analysis_job_repo,
        profile_repo=profile_repo,
        config=analyze_config,
        composer=composer,
        tracker=tracker,
    )
