"""End-to-end: PUT brand profile → composer → brand_placement_settings.

Exercises the full Hook A wire path (COR-56):

    PUT /v1/brand/{id}/profile
        → BrandService.upsert_profile commit
        → asyncio.create_task(composer.compose) (Hook A)
        → tracker.track
        → lifespan shutdown drains tracker
        → brand_placement_settings row visible.

The lifespan-shutdown drain is the synchronisation point: when the
``with TestClient(...)`` block exits, the lifespan handler awaits the
composer task before tearing down. After the ``with`` block, the row
MUST be present.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from cortex_api.app.dependencies.auth import authenticated_user
from cortex_api.core.identifiers import uuid7
from cortex_api.infra.container import Container as InfraContainer
from cortex_api.main import create_app
from cortex_api.service.brand.model.profile import BrandProfile
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.brand_identity.model.brand import Brand
from cortex_api.service.identity.model.authed_user import AuthedUser
from cortex_api.service.placement.model.settings import (
    BrandPlacementSettings,
    PlacementMode,
)
from cortex_api.service.placement.model.status import PlacementRowStatus
from cortex_api.service.placement.repo.settings_repo import PlacementSettingsRepo

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
async def _schema() -> None:
    from sqlmodel import SQLModel

    db = InfraContainer()._database_client_factory()
    async with db.session() as s:
        conn = await s.connection()
        await conn.run_sync(SQLModel.metadata.create_all)


def _authed(brand_id, caps):  # noqa: ANN001
    return AuthedUser(
        user_id=uuid7(),
        email="t@example.com",
        display_name="T",
        raw_claims={
            "active_context": {
                "kind": "brand",
                "id": str(brand_id),
                "role": "admin",
                "capabilities": caps,
            }
        },
    )


@pytest.fixture
async def brand_id():
    bid = uuid7()
    db = InfraContainer()._database_client_factory()
    async with db.session() as s:
        s.add(Brand(id=bid, display_name="ComposerCo"))
        await s.flush()
    return bid


async def test_put_profile_triggers_composer_and_writes_settings_row(brand_id) -> None:
    app = create_app()
    app.dependency_overrides[authenticated_user] = lambda: _authed(
        brand_id, ["view_brand_dashboard", "edit_brand_settings"]
    )
    with TestClient(app) as c:
        put = c.put(
            f"/v1/brand/{brand_id}/profile",
            json={
                "name": "ComposerCo",
                "tagline": "Tag line",
                "about": "An about blurb",
                "source_url": "https://composerco.example/",
                "category": {
                    "value": "books",
                    "alternatives": ["literature", "nonfiction"],
                },
                "products": [{"name": "Hardcover"}, {"name": "Audiobook"}],
                "competitors": [{"name": "Rival Press"}],
            },
        )
        assert put.status_code == 200, put.text
    # Lifespan shutdown (triggered by TestClient ``with`` exit) drained the
    # composer task. The settings row MUST now exist.

    db = InfraContainer()._database_client_factory()
    async with db.session() as s:
        saved = await PlacementSettingsRepo().get_or_none(s, brand_id)

    assert saved is not None, "composer did not write brand_placement_settings"
    assert saved.brand_id == brand_id
    assert saved.brand_cta_text == "Learn more about ComposerCo"
    assert saved.brand_cta_url == "https://composerco.example/"
    assert saved.matching_categories == ["literature", "nonfiction"]
    assert saved.matching_keywords == ["Hardcover", "Audiobook", "Rival Press"]
    assert saved.ad_ratio == Decimal("1.00")
    assert saved.mode == PlacementMode.QUESTION_REPLACEMENT
    assert saved.question_position == 1
    assert saved.status == PlacementRowStatus.ACTIVE
    assert saved.overrides_mask == {}
    # composed_at is the canonical "row is placement-ready" predicate (per
    # the model docstring). Composer MUST stamp it on every successful run.
    assert saved.composed_at is not None


async def test_placement_sweep_reclaims_brand_with_missing_settings(brand_id) -> None:
    """PR #52 Issue 3: a brand_profile committed without a placement
    settings row (durability gap from SIGKILL between Hook A scheduling
    and the composer task running) is recovered by the periodic sweep.
    Mirrors the analyze pipeline's stale-sweep pattern.
    """
    from cortex_api import main as _main

    # Seed a profile but DO NOT run the composer — simulate the gap.
    db = InfraContainer()._database_client_factory()
    async with db.session() as s:
        await BrandProfileRepo().upsert(
            s,
            BrandProfile(
                brand_id=brand_id,
                name="Orphan Co",
                category_value="news",
                category_alternatives=["media"],
            ),
        )
        # Sanity: no placement row yet.
        assert (await PlacementSettingsRepo().get_or_none(s, brand_id)) is None

    reclaimed = await _main._placement_sweep_iteration(limit=100)
    assert reclaimed >= 1

    # Drain the composer tasks the sweep scheduled.
    await _main._placement_container.tracker().drain()

    async with db.session() as s:
        saved = await PlacementSettingsRepo().get_or_none(s, brand_id)
    assert saved is not None
    assert saved.brand_id == brand_id
    assert saved.composed_at is not None  # quality gate passes (category present)


async def test_placement_sweep_reclaims_when_profile_updated_after_settings(brand_id) -> None:
    """Profile rewritten after the last compose — sweep re-fires the
    composer so derived fields catch up with the fresh profile.

    The natural sequence: first compose stamps a settings row, then a
    follow-up profile rewrite bumps ``brand_profile.updated_at`` past
    ``brand_placement_settings.updated_at``; sweep picks up the drift.
    """
    from cortex_api import main as _main

    db = InfraContainer()._database_client_factory()
    # 1. Seed profile + run an initial compose so settings.updated_at exists.
    async with db.session() as s:
        await BrandProfileRepo().upsert(
            s,
            BrandProfile(
                brand_id=brand_id,
                name="Drift Co",
                category_value="news",
                category_alternatives=["old_category"],
            ),
        )
    await _main._brand_container.composer().compose(brand_id)

    # 2. Rewrite the profile — onupdate bumps profile.updated_at past
    #    the settings row's updated_at, producing the drift the sweep
    #    is meant to catch.
    async with db.session() as s:
        await BrandProfileRepo().upsert(
            s,
            BrandProfile(
                brand_id=brand_id,
                name="Drift Co",
                category_value="news",
                category_alternatives=["media"],
            ),
        )

    reclaimed = await _main._placement_sweep_iteration(limit=100)
    assert reclaimed >= 1
    await _main._placement_container.tracker().drain()

    async with db.session() as s:
        saved = await PlacementSettingsRepo().get_or_none(s, brand_id)
    assert saved is not None
    # Categories now reflect the rewritten profile.
    assert saved.matching_categories == ["media"]


async def test_placement_sweep_skips_brands_already_composed(brand_id) -> None:
    """If the settings row is at-least-as-fresh as the profile, the
    sweep MUST NOT re-fire — otherwise it busy-loops on every brand.
    """
    from cortex_api import main as _main

    db = InfraContainer()._database_client_factory()
    async with db.session() as s:
        await BrandProfileRepo().upsert(
            s,
            BrandProfile(brand_id=brand_id, name="Fresh Co", category_value="news"),
        )

    # Run compose once (via sweep is fine).
    await _main._placement_sweep_iteration(limit=100)
    await _main._placement_container.tracker().drain()

    # Second sweep must report 0 reclaimed.
    second = await _main._placement_sweep_iteration(limit=100)
    assert second == 0


async def test_concurrent_composes_preserve_overrides_mask(brand_id) -> None:
    """PR #52 Issue 2: two concurrent ``compose`` calls on the same
    ``brand_id`` must not lose the ``overrides_mask`` invariant. The
    repo's SELECT FOR UPDATE serialises the read-derive-merge-write
    cycle — both writers observe the mask and preserve the user's
    hand-tuned matching_rules.
    """
    from cortex_api import main as _main

    # Seed: brand_profile with category (passes quality gate) + an
    # existing settings row whose overrides_mask anchors the user's
    # hand-tuned matching_rules.
    db = InfraContainer()._database_client_factory()
    async with db.session() as s:
        await BrandProfileRepo().upsert(
            s,
            BrandProfile(
                brand_id=brand_id,
                name="Racing Co",
                category_value="cars",
                category_alternatives=["motorsport"],
            ),
        )
        await PlacementSettingsRepo().upsert(
            s,
            BrandPlacementSettings(
                brand_id=brand_id,
                matching_rules="HAND_TUNED — must survive concurrent composes",
                matching_categories=["motorsport"],
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
            ),
        )

    composer = _main._brand_container.composer()
    await asyncio.gather(composer.compose(brand_id), composer.compose(brand_id))

    async with db.session() as s:
        saved = await PlacementSettingsRepo().get_or_none(s, brand_id)

    assert saved is not None
    # User's hand-tuned value preserved through BOTH composes.
    assert saved.matching_rules == "HAND_TUNED — must survive concurrent composes"
    assert saved.overrides_mask == {"matching_rules": True}
    # Quality gate satisfied (category present), so composed_at stamped.
    assert saved.composed_at is not None
