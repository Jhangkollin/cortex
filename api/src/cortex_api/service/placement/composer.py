"""BrandPlacementComposer — re-materialises ``brand_placement_settings``.

Spec: AD7 in ``aigc_coordinator/placement-runtime-design.md``. Template-only
derivation at MVP (no LLM). Two fire-and-forget hook points wire this in:
``BrandService.upsert_profile`` (Hook A) and ``AnalyzeJobService._run`` success
branch (Hook B) — both schedule ``compose`` via ``asyncio.create_task``.

The composer is idempotent: re-running with the same profile produces the
same row, except ``composed_at`` advances. ``overrides_mask`` (D1/D2) is
honoured by ``_apply_overrides``: keys marked ``true`` keep the existing
row's value across re-derivation; everything else is replaced.

**``composed_at`` quality gate (PR #52 Issue 1):** ``composed_at IS NOT
NULL`` is the documented "placement-ready" predicate downstream consumers
gate on (see ``model/settings.py`` docstring). Stamping it on garbage —
e.g. a profile with no category and no products produces ``"Match articles
related to  and "`` — would route placement decisions through empty
templates. The gate at ``_is_placement_ready`` requires at least one
actionable matching signal (either profile-derived OR user-overridden
via mask) before stamping ``composed_at``. The row itself is still
written so any pre-existing mask state persists across re-derivations;
``composed_at = NULL`` simply means "tried, not ready yet."
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

import structlog

from cortex_api.core.exceptions import NotFoundError
from cortex_api.infra.database_client import DatabaseClient
from cortex_api.service.brand.model.profile import BrandProfile
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.placement.cache.eligible_brands_cache import EligibleBrandsCache
from cortex_api.service.placement.model.settings import (
    BrandPlacementSettings,
    PlacementMode,
)
from cortex_api.service.placement.model.status import PlacementRowStatus
from cortex_api.service.placement.repo.settings_repo import PlacementSettingsRepo

_DERIVED_FIELDS: tuple[str, ...] = (
    "matching_rules",
    "matching_categories",
    "matching_keywords",
    "brand_question_prompt",
    "brand_answer_prompt",
    "brand_cta_text",
    "brand_cta_url",
    "ad_ratio",
    "mode",
    "question_position",
    "status",
)


class BrandPlacementComposer:
    """Re-materialises a brand's placement settings from its profile."""

    def __init__(
        self,
        database_client: DatabaseClient,
        profile_repo: BrandProfileRepo,
        settings_repo: PlacementSettingsRepo,
        cache: EligibleBrandsCache,
    ) -> None:
        self._logger = structlog.get_logger(__name__)
        self._db = database_client
        self._profiles = profile_repo
        self._settings = settings_repo
        self._cache = cache

    async def compose(self, brand_id: UUID) -> None:
        async with self._db.session() as session:
            profile = await self._profiles.get(session, brand_id)
            if profile is None:
                raise NotFoundError(f"brand profile for {brand_id} not found")
            existing = await self._settings.get_or_none_for_update(session, brand_id)
            mask = existing.overrides_mask if existing else {}
            derived = self._derive_from_profile(profile)
            merged = self._apply_overrides(brand_id, derived, existing, mask, profile=profile)
            await self._settings.upsert(session, merged)
        # Post-commit cache invalidate — fires AFTER the session closes so
        # readers never see the cache cleared before the committed row is
        # visible. Invalidate on EVERY successful upsert, including the
        # regression direction (composed_at: ts → None) — without this, a
        # brand that loses eligibility (e.g., category + products removed)
        # would stay in the cached payload until TTL expiry (up to 300s),
        # serving stale "eligible" to agent-ws callers. The cache's own
        # implementation swallows Redis-down errors; trust it.
        await self._cache.invalidate_for_brand(brand_id=brand_id)
        self._logger.info(
            "placement_composed",
            brand_id=str(brand_id),
            placement_ready=merged.composed_at is not None,
        )

    def _derive_from_profile(self, profile: BrandProfile) -> dict[str, Any]:
        category_value = profile.category_value or ""
        alternatives = profile.category_alternatives or []
        products = profile.products or []
        competitors = profile.competitors or []
        keywords = [p.get("name") for p in products if p.get("name")]
        keywords.extend(c.get("name") for c in competitors if c.get("name"))
        return {
            "matching_rules": (f"Match articles related to {category_value} and {', '.join(alternatives)}"),
            "matching_categories": list(alternatives),
            "matching_keywords": keywords,
            "brand_question_prompt": (
                f"Generate a brand-aware question for {profile.name}. Tagline: {profile.tagline or ''}"
            ),
            "brand_answer_prompt": (
                f"Generate a brand-aware answer for {profile.name}. "
                f"About: {profile.about or ''}. Products: {len(products)} item(s)."
            ),
            "brand_cta_text": f"Learn more about {profile.name}",
            "brand_cta_url": profile.source_url,
            "ad_ratio": Decimal("1.00"),
            "mode": PlacementMode.QUESTION_REPLACEMENT,
            "question_position": 1,
            "status": PlacementRowStatus.ACTIVE,
        }

    def _apply_overrides(
        self,
        brand_id: UUID,
        derived: dict[str, Any],
        existing: BrandPlacementSettings | None,
        mask: dict[str, bool],
        *,
        profile: BrandProfile,
    ) -> BrandPlacementSettings:
        values: dict[str, Any] = dict(derived)
        if existing is not None:
            for field in _DERIVED_FIELDS:
                if mask.get(field):
                    values[field] = getattr(existing, field)
        composed_at = datetime.utcnow() if self._is_placement_ready(profile, values, mask) else None
        return BrandPlacementSettings(
            brand_id=brand_id,
            overrides_mask=dict(mask),
            composed_at=composed_at,
            **values,
        )

    @staticmethod
    def _is_placement_ready(
        profile: BrandProfile,
        merged_values: dict[str, Any],
        mask: dict[str, bool],
    ) -> bool:
        """Quality gate for ``composed_at``: at least one actionable
        matching signal must be present, either from the profile itself
        OR from a user-overridden mask entry.

        User-overridden fields are by definition human-entered; trust
        them over the derived template (which is degenerate when both
        ``category_value`` and ``category_alternatives`` are empty).
        """
        for field in ("matching_rules", "matching_categories", "matching_keywords"):
            if mask.get(field) and merged_values.get(field):
                return True
        if profile.category_value or profile.category_alternatives:
            return True
        return bool(profile.products or profile.competitors)
