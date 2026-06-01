"""BrandPlacementComposer (COR-56) — unit tests.

Composer maps a `BrandProfile` row to a `BrandPlacementSettings` row using
the template-only derivation per AD7. No LLM. The test IS the spec for the
template shapes — keep the assertions explicit so future template changes
require a deliberate test edit.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from cortex_api.core.exceptions import NotFoundError
from cortex_api.core.identifiers import uuid7
from cortex_api.service.brand.model.profile import BrandProfile
from cortex_api.service.placement.cache.eligible_brands_cache import EligibleBrandsCache
from cortex_api.service.placement.composer import BrandPlacementComposer
from cortex_api.service.placement.model.settings import (
    BrandPlacementSettings,
    PlacementMode,
)
from cortex_api.service.placement.model.status import PlacementRowStatus


class _FakeSessionCtx:
    async def __aenter__(self) -> object:
        return object()

    async def __aexit__(self, *_: object) -> bool:
        return False


class _FakeDB:
    def session(self) -> _FakeSessionCtx:
        return _FakeSessionCtx()


class _FakeProfileRepo:
    def __init__(self, profile: BrandProfile | None = None) -> None:
        self._profile = profile

    async def get(self, _session: object, _brand_id: UUID) -> BrandProfile | None:
        return self._profile


class _FakeSettingsRepo:
    def __init__(self, existing: BrandPlacementSettings | None = None) -> None:
        self.existing = existing
        self.upserts: list[BrandPlacementSettings] = []

    async def get_or_none(self, _session: object, _brand_id: UUID) -> BrandPlacementSettings | None:
        return self.existing

    async def get_or_none_for_update(self, _session: object, _brand_id: UUID) -> BrandPlacementSettings | None:
        # Same behaviour as get_or_none in-memory; production code uses the
        # Postgres FOR UPDATE variant — see settings_repo.py.
        return self.existing

    async def upsert(self, _session: object, settings: BrandPlacementSettings) -> BrandPlacementSettings:
        self.upserts.append(settings)
        return settings


def _composer(
    profile: BrandProfile | None,
    existing: BrandPlacementSettings | None = None,
    cache: EligibleBrandsCache | None = None,
) -> tuple[BrandPlacementComposer, _FakeSettingsRepo]:
    settings_repo = _FakeSettingsRepo(existing=existing)
    composer = BrandPlacementComposer(
        database_client=_FakeDB(),
        profile_repo=_FakeProfileRepo(profile=profile),
        settings_repo=settings_repo,
        cache=cache if cache is not None else AsyncMock(spec=EligibleBrandsCache),
    )
    return composer, settings_repo


def _sample_profile(brand_id: UUID) -> BrandProfile:
    return BrandProfile(
        brand_id=brand_id,
        name="Acme Coffee",
        tagline="Roasted with care.",
        about="Specialty coffee roaster founded 2018",
        source_url="https://acmecoffee.example/",
        category_value="specialty_coffee",
        category_alternatives=["coffee", "roastery"],
        products=[{"name": "Espresso Beans"}, {"name": "Cold Brew Kit"}],
        competitors=[{"name": "Blue Bottle"}],
    )


async def test_compose_raises_when_profile_missing() -> None:
    composer, settings_repo = _composer(profile=None)
    with pytest.raises(NotFoundError):
        await composer.compose(uuid7())
    assert settings_repo.upserts == []


async def test_compose_writes_derived_settings_when_no_existing_row() -> None:
    bid = uuid7()
    composer, settings_repo = _composer(profile=_sample_profile(bid))

    await composer.compose(bid)

    assert len(settings_repo.upserts) == 1
    saved = settings_repo.upserts[0]
    assert saved.brand_id == bid
    assert saved.matching_rules == "Match articles related to specialty_coffee and coffee, roastery"
    assert saved.matching_categories == ["coffee", "roastery"]
    assert saved.matching_keywords == ["Espresso Beans", "Cold Brew Kit", "Blue Bottle"]
    assert saved.brand_question_prompt == (
        "Generate a brand-aware question for Acme Coffee. Tagline: Roasted with care."
    )
    assert saved.brand_answer_prompt == (
        "Generate a brand-aware answer for Acme Coffee. "
        "About: Specialty coffee roaster founded 2018. Products: 2 item(s)."
    )
    assert saved.brand_cta_text == "Learn more about Acme Coffee"
    assert saved.brand_cta_url == "https://acmecoffee.example/"
    assert saved.ad_ratio == Decimal("1.00")
    assert saved.mode == PlacementMode.QUESTION_REPLACEMENT
    assert saved.question_position == 1
    assert saved.status == PlacementRowStatus.ACTIVE
    assert saved.overrides_mask == {}
    assert saved.composed_at is not None


async def test_compose_preserves_fields_marked_in_overrides_mask() -> None:
    bid = uuid7()
    existing = BrandPlacementSettings(
        brand_id=bid,
        matching_rules="HAND_TUNED rule that must NOT be overwritten",
        brand_cta_text="Custom CTA",
        matching_categories=["coffee", "roastery"],
        matching_keywords=["Espresso Beans", "Cold Brew Kit", "Blue Bottle"],
        brand_question_prompt="placeholder",
        brand_answer_prompt="placeholder",
        brand_cta_url="https://acmecoffee.example/",
        ad_ratio=Decimal("1.00"),
        mode=PlacementMode.QUESTION_REPLACEMENT,
        question_position=1,
        status=PlacementRowStatus.ACTIVE,
        overrides_mask={"matching_rules": True, "brand_cta_text": True},
    )
    composer, settings_repo = _composer(profile=_sample_profile(bid), existing=existing)

    await composer.compose(bid)

    saved = settings_repo.upserts[0]
    # Marked fields preserved from existing row.
    assert saved.matching_rules == "HAND_TUNED rule that must NOT be overwritten"
    assert saved.brand_cta_text == "Custom CTA"
    # Mask itself preserved so subsequent composes keep honouring it.
    assert saved.overrides_mask == {"matching_rules": True, "brand_cta_text": True}
    # Unmasked derived fields still re-derived from the (refreshed) profile.
    assert saved.matching_categories == ["coffee", "roastery"]
    assert saved.brand_question_prompt == (
        "Generate a brand-aware question for Acme Coffee. Tagline: Roasted with care."
    )
    # Every compose advances composed_at.
    assert saved.composed_at is not None


async def test_compose_writes_row_but_leaves_composed_at_null_when_no_match_signals() -> None:
    """Quality gate (PR #52 Issue 1): the derived row is written so any
    pre-existing overrides_mask state persists, but ``composed_at`` is
    left NULL — eligible-brands consumers gating on ``composed_at IS NOT
    NULL`` will correctly skip this brand until the profile gains
    actionable matching data.
    """
    bid = uuid7()
    minimal = BrandProfile(brand_id=bid, name="Bare Co")
    composer, settings_repo = _composer(profile=minimal)

    await composer.compose(bid)

    saved = settings_repo.upserts[0]
    assert saved.brand_id == bid
    # Row is written so the mask state persists across re-derivations.
    assert saved.matching_categories == []
    assert saved.matching_keywords == []
    assert saved.brand_cta_text == "Learn more about Bare Co"
    # Quality gate: NOT placement-ready.
    assert saved.composed_at is None


async def test_compose_stamps_composed_at_when_profile_has_categories_only() -> None:
    """A profile with a category but no products/competitors still counts
    as actionable — categories alone are a valid match signal.
    """
    bid = uuid7()
    profile = BrandProfile(
        brand_id=bid,
        name="Category Only Co",
        category_value="books",
        category_alternatives=["literature"],
    )
    composer, settings_repo = _composer(profile=profile)

    await composer.compose(bid)

    saved = settings_repo.upserts[0]
    assert saved.matching_categories == ["literature"]
    assert saved.composed_at is not None


async def test_compose_stamps_composed_at_when_only_user_overrides_provide_signal() -> None:
    """Even with an empty profile, a user-overridden matching field (via
    mask) is by definition human-entered and meaningful — the row IS
    placement-ready.
    """
    bid = uuid7()
    minimal = BrandProfile(brand_id=bid, name="Override Only Co")
    existing = BrandPlacementSettings(
        brand_id=bid,
        matching_rules="Hand-tuned rule the user actually wants",
        matching_categories=[],
        matching_keywords=[],
        brand_question_prompt="placeholder",
        brand_answer_prompt="placeholder",
        brand_cta_text="placeholder",
        brand_cta_url=None,
        ad_ratio=Decimal("1.00"),
        mode=PlacementMode.QUESTION_REPLACEMENT,
        question_position=1,
        status=PlacementRowStatus.ACTIVE,
        overrides_mask={"matching_rules": True},
    )
    composer, settings_repo = _composer(profile=minimal, existing=existing)

    await composer.compose(bid)

    saved = settings_repo.upserts[0]
    assert saved.matching_rules == "Hand-tuned rule the user actually wants"
    assert saved.composed_at is not None


class TestComposerCacheInvalidation:
    @pytest.mark.asyncio
    async def test_invalidate_called_after_successful_compose(self) -> None:
        """When _is_placement_ready returns True (composed_at is not None),
        invalidate_for_brand must be awaited exactly once post-commit."""
        bid = uuid7()
        cache = AsyncMock(spec=EligibleBrandsCache)
        # _sample_profile has category_value + products → placement-ready
        composer, _ = _composer(profile=_sample_profile(bid), cache=cache)

        await composer.compose(bid)

        cache.invalidate_for_brand.assert_awaited_once_with(brand_id=bid)

    @pytest.mark.asyncio
    async def test_invalidate_called_when_quality_gate_fails(self) -> None:
        """When _is_placement_ready returns False (composed_at is None),
        invalidate_for_brand MUST still be awaited — a brand that regresses
        from placement-ready to not-ready must be flushed from cache
        immediately so F2 stops returning it (otherwise stale up to TTL).
        """
        bid = uuid7()
        cache = AsyncMock(spec=EligibleBrandsCache)
        # Minimal profile → quality gate fails → composed_at stays None
        minimal = BrandProfile(brand_id=bid, name="Bare Co")
        composer, _ = _composer(profile=minimal, cache=cache)

        await composer.compose(bid)

        cache.invalidate_for_brand.assert_awaited_once_with(brand_id=bid)
