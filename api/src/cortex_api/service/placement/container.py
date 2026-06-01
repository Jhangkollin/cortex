"""Placement DI container — shared singletons (no composer).

The composer itself is provided by ``service.brand.container`` because its
constructor needs ``BrandProfileRepo`` (a brand-owned singleton); wiring
it here would make Placement depend back on Brand. Keeping the composer
in the brand container lets the dependency graph stay one-way (Brand →
Placement) while the *class definition* lives at
``service/placement/composer.py`` where it semantically belongs.

What lives here:

* ``tracker`` — process-wide ``BackgroundTaskTracker`` consumed by every
  hook site (currently Brand + Analyze) and drained at lifespan
  shutdown. Singleton.
* ``settings_repo`` — stateless CRUD for ``brand_placement_settings``;
  composer is the only writer at MVP. Singleton (cheap, no state).
"""

from dependency_injector import containers, providers

from cortex_api.core.background import BackgroundTaskTracker
from cortex_api.service.placement.repo.eligible_brands_repo import EligibleBrandsRepo
from cortex_api.service.placement.repo.scope_repo import BrandPublisherScopeRepo
from cortex_api.service.placement.repo.settings_repo import PlacementSettingsRepo


class Container(containers.DeclarativeContainer):
    """DI container for the placement domain's shared singletons."""

    tracker: providers.Provider[BackgroundTaskTracker] = providers.Singleton(BackgroundTaskTracker)
    settings_repo: providers.Provider[PlacementSettingsRepo] = providers.Singleton(PlacementSettingsRepo)

    # Stateless repos consumed by EligibleBrandsCache + EligibleBrandsService.
    eligible_brands_repo: providers.Provider[EligibleBrandsRepo] = providers.Singleton(EligibleBrandsRepo)
    scope_repo: providers.Provider[BrandPublisherScopeRepo] = providers.Singleton(BrandPublisherScopeRepo)
