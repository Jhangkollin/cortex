from unittest.mock import MagicMock

import pytest
from dependency_injector import providers
from dependency_injector.errors import Error

from cortex_api.core.background import BackgroundTaskTracker
from cortex_api.service.brand.container import Container
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.brand.service import BrandService
from cortex_api.service.placement.cache.eligible_brands_cache import EligibleBrandsCache
from cortex_api.service.placement.repo.eligible_brands_repo import EligibleBrandsRepo
from cortex_api.service.placement.repo.settings_repo import PlacementSettingsRepo


def test_container_provides_wired_service() -> None:
    """``BrandContainer`` requires explicit wiring of all four placement-owned
    singletons (tracker, settings_repo, eligible_brands_cache, eligible_brands_repo)
    via constructor args — mirrors main.py's composition root.

    This protects against the footgun flagged in PR #52 Issue 4: any
    code path that constructs ``BrandContainer()`` without wiring these
    will raise ``DependencyError``, not silently get a duplicate tracker.
    """
    c = Container(
        tracker=providers.Singleton(BackgroundTaskTracker),
        settings_repo=providers.Singleton(PlacementSettingsRepo),
        eligible_brands_cache=providers.Object(MagicMock(spec=EligibleBrandsCache)),
        eligible_brands_repo=providers.Singleton(EligibleBrandsRepo),
    )
    svc = c.service()
    assert isinstance(svc, BrandService)
    assert isinstance(c.profile_repo(), BrandProfileRepo)
    assert c.service() is svc  # singleton


def test_container_without_wiring_raises_dependency_error() -> None:
    """Regression guard: BrandContainer() with no overrides must fail loudly
    when any Dependency provider is resolved — not return a BrandService
    bound to an orphan tracker.

    Wiring only tracker + settings_repo (missing the two new cache/repo deps)
    still raises DependencyError, confirming all four deps must be supplied.
    """
    c = Container(
        tracker=providers.Singleton(BackgroundTaskTracker),
        settings_repo=providers.Singleton(PlacementSettingsRepo),
        # eligible_brands_cache and eligible_brands_repo intentionally omitted
    )
    with pytest.raises(Error, match="not defined"):
        c.service()


def test_container_fully_wired_resolves_eligible_brands_service() -> None:
    """Positive test: all four deps supplied → eligible_brands_service resolves."""
    from cortex_api.service.placement.service.eligible_brands_service import EligibleBrandsService

    c = Container(
        tracker=providers.Singleton(BackgroundTaskTracker),
        settings_repo=providers.Singleton(PlacementSettingsRepo),
        eligible_brands_cache=providers.Object(MagicMock(spec=EligibleBrandsCache)),
        eligible_brands_repo=providers.Singleton(EligibleBrandsRepo),
    )
    svc = c.eligible_brands_service()
    assert isinstance(svc, EligibleBrandsService)
    assert c.eligible_brands_service() is svc  # singleton
