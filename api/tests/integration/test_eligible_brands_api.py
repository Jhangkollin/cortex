"""Integration tests for F2 GET /v1/publishers/{uuid}/eligible-brands.

Requires: docker-compose Postgres on :5433, Redis on :6379.

Pattern (mirrors ``test_placement_composer.py``):
- Async test bodies create their own ``app = create_app()`` and open
  ``TestClient(app)`` inline. This keeps the brand-container singletons
  bound to one loop per test (TestClient's portal loop), avoiding the
  cross-event-loop hazard that arises when the conftest ``client``
  fixture starts the app lifespan on a separate loop *before* an
  async-fixture seed runs.
- Seeding is via direct INSERT (not via ``composer.compose``). The
  composer's cache-invalidate post-commit hook is covered by unit tests
  (``test_composer.py``, ``test_eligible_brands_cache.py``); the
  integration suite focuses on the F2 read-path contract.
- Sync auth tests reuse the conftest ``client`` fixture because they
  never touch DB-bearing fixtures, so cross-loop binding isn't triggered.
"""

from __future__ import annotations

import datetime as _dt
import os
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

VALID_TOKEN = "test-token-for-integration"
INVALID_TOKEN = "wrong-token"

pytestmark = pytest.mark.integration


def _create_app_with_service_token():
    """Build a fresh app whose ServiceBearerMiddleware uses ``VALID_TOKEN``.

    ``ServiceTokenConfig`` is a Singleton wired into ``CoreContainer``. The
    instance is cached at ``main.py`` first-import — which, in alphabetical
    collection order, happens before this module's top-level code runs (some
    earlier test modules import ``cortex_api.main`` at top level). Setting
    the env var at module import is therefore racy. Reset the singleton
    explicitly here so ``create_app()`` reads the env we want.
    """
    from cortex_api import main as _main
    from cortex_api.main import create_app

    os.environ["CORE_SERVICE_TOKEN_AGENT_WS"] = VALID_TOKEN
    _main._core_container.service_token_config.reset()
    return create_app()


# Sentinel meaning "leave composed_at NULL" — distinct from the seed helper's
# default (now()). The quality-gate test passes this to verify F2 excludes
# rows the composer hasn't yet certified.
_NO_COMPOSED_AT = object()


def _fresh_db():
    """Return a fresh DatabaseClient via a transient InfraContainer.

    Mirrors ``test_placement_composer.py``'s pattern: each call builds its
    own InfraContainer instance, so the resulting DatabaseClient's engine
    binds to the current event loop only and is GC-eligible at fixture
    teardown — no cross-test loop reuse.
    """
    from cortex_api.infra.container import Container as InfraContainer

    return InfraContainer()._database_client_factory()


async def _seed_eligible_brand(
    *,
    publisher_uuid: UUID,
    name: str = "TechBrand",
    about: str | None = "A test brand",
    topics: list[str] | None = None,
    matching_rules: str | None = None,
    matching_keywords: list[str] | None = None,
    matching_categories: list[str] | None = None,
    composed_at=None,  # noqa: ANN001 — datetime | None | _NO_COMPOSED_AT
    lang: str = "zh-tw",
) -> UUID:
    """Insert Brand + Profile + Scope + placement-settings as one row.

    ``composed_at=None`` (default) stamps "now" — the quality gate's
    placement-ready predicate is satisfied. Pass ``_NO_COMPOSED_AT`` to
    leave the column NULL (incomplete row, must be excluded by F2).
    """
    from cortex_api.core.identifiers import uuid7
    from cortex_api.service.brand.model.profile import BrandProfile
    from cortex_api.service.brand_identity.model.brand import Brand
    from cortex_api.service.placement.model.scope import BrandPublisherScope
    from cortex_api.service.placement.model.settings import (
        BrandPlacementSettings,
        PlacementMode,
    )
    from cortex_api.service.placement.model.status import PlacementRowStatus

    if composed_at is _NO_COMPOSED_AT:
        effective_composed_at = None
    elif composed_at is None:
        effective_composed_at = _dt.datetime.now(tz=_dt.UTC).replace(tzinfo=None)
    else:
        effective_composed_at = composed_at

    brand_uuid = uuid7()
    db = _fresh_db()
    async with db.session() as s:
        s.add(Brand(id=brand_uuid, display_name=name))
        await s.flush()
        s.add(
            BrandProfile(
                brand_id=brand_uuid,
                name=name,
                about=about,
                topics=topics or [],
            )
        )
        s.add(
            BrandPublisherScope(
                brand_id=brand_uuid,
                publisher_id=publisher_uuid,
                lang=lang,
                status=PlacementRowStatus.ACTIVE,
            )
        )
        s.add(
            BrandPlacementSettings(
                brand_id=brand_uuid,
                matching_rules=matching_rules,
                matching_keywords=matching_keywords or [],
                matching_categories=matching_categories or [],
                ad_ratio=Decimal("1.00"),
                question_position=1,
                mode=PlacementMode.QUESTION_REPLACEMENT,
                status=PlacementRowStatus.ACTIVE,
                composed_at=effective_composed_at,
            )
        )
        await s.flush()
    return brand_uuid


# ---------------------------------------------------------------------------
# Auth tests — sync, reuse conftest's ``client`` fixture
# ---------------------------------------------------------------------------


class TestEligibleBrandsAuthentication:
    """ServiceBearerMiddleware enforces Bearer on /v1/publishers/*.

    Each test builds its own app via ``_create_app_with_service_token()``
    so the middleware is wired with a known, non-empty token — otherwise
    test_wrong_token would pass vacuously (empty configured token also
    rejects every request).
    """

    def test_missing_token_returns_401(self) -> None:
        from fastapi.testclient import TestClient

        app = _create_app_with_service_token()
        publisher_uuid = uuid4()
        with TestClient(app) as c:
            r = c.get(f"/v1/publishers/{publisher_uuid}/eligible-brands?lang=zh-tw")
        assert r.status_code == 401
        assert r.headers.get("www-authenticate", "").startswith("Bearer")

    def test_wrong_token_returns_401(self) -> None:
        from fastapi.testclient import TestClient

        app = _create_app_with_service_token()
        publisher_uuid = uuid4()
        with TestClient(app) as c:
            r = c.get(
                f"/v1/publishers/{publisher_uuid}/eligible-brands?lang=zh-tw",
                headers={"Authorization": f"Bearer {INVALID_TOKEN}"},
            )
        assert r.status_code == 401

    def test_brand_route_not_affected_by_middleware(self) -> None:
        from fastapi.testclient import TestClient

        app = _create_app_with_service_token()
        with TestClient(app) as c:
            r = c.get("/v1/brand/00000000-0000-0000-0000-000000000001/profile")
        assert r.status_code in (401, 404, 422)
        wwwauth = r.headers.get("www-authenticate", "")
        assert 'realm="cortex-service"' not in wwwauth


# ---------------------------------------------------------------------------
# Happy path + quality gate — async, inline TestClient
# ---------------------------------------------------------------------------


class TestEligibleBrandsHappyPath:
    """F2 returns the right rows for placement-ready brands."""

    async def test_returns_200_with_eligible_brand(self) -> None:
        from fastapi.testclient import TestClient

        publisher_uuid = uuid4()
        brand_uuid = await _seed_eligible_brand(
            publisher_uuid=publisher_uuid,
            name="TechBrand",
            about="A tech brand",
            topics=["ai", "robotics"],
            matching_keywords=["llm"],
            matching_categories=["tech"],
        )

        app = _create_app_with_service_token()
        with TestClient(app) as c:
            r = c.get(
                f"/v1/publishers/{publisher_uuid}/eligible-brands?lang=zh-tw",
                headers={"Authorization": f"Bearer {VALID_TOKEN}"},
            )
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body, list)
        assert len(body) == 1
        row = body[0]
        assert UUID(row["brand_uuid"]) == brand_uuid
        assert row["brand_name"] == "TechBrand"
        assert row["brand_description"] == "A tech brand"
        assert row["brand_topics"] == ["ai", "robotics"]
        assert row["matching_keywords"] == ["llm"]
        assert row["matching_categories"] == ["tech"]
        assert row["ad_ratio"] == 1.0
        assert row["question_position"] == 1
        assert row["mode"] == "question_replacement"

    def test_returns_empty_list_for_unknown_publisher(self) -> None:
        from fastapi.testclient import TestClient

        app = _create_app_with_service_token()
        unknown = uuid4()
        with TestClient(app) as c:
            r = c.get(
                f"/v1/publishers/{unknown}/eligible-brands?lang=zh-tw",
                headers={"Authorization": f"Bearer {VALID_TOKEN}"},
            )
        assert r.status_code == 200
        assert r.json() == []

    async def test_lang_mismatch_returns_empty(self) -> None:
        from fastapi.testclient import TestClient

        publisher_uuid = uuid4()
        await _seed_eligible_brand(publisher_uuid=publisher_uuid, lang="zh-tw")

        app = _create_app_with_service_token()
        with TestClient(app) as c:
            r = c.get(
                f"/v1/publishers/{publisher_uuid}/eligible-brands?lang=en-us",
                headers={"Authorization": f"Bearer {VALID_TOKEN}"},
            )
        assert r.status_code == 200
        assert r.json() == []


class TestEligibleBrandsQualityGate:
    """Brands with ``composed_at IS NULL`` must be excluded from F2."""

    async def test_excludes_brand_with_null_composed_at(self) -> None:
        from fastapi.testclient import TestClient

        publisher_uuid = uuid4()
        await _seed_eligible_brand(
            publisher_uuid=publisher_uuid,
            name="IncompleteBrand",
            composed_at=_NO_COMPOSED_AT,
        )

        app = _create_app_with_service_token()
        with TestClient(app) as c:
            r = c.get(
                f"/v1/publishers/{publisher_uuid}/eligible-brands?lang=zh-tw",
                headers={"Authorization": f"Bearer {VALID_TOKEN}"},
            )
        assert r.status_code == 200
        assert r.json() == []


# ---------------------------------------------------------------------------
# Write-through cache invalidation
#
# Composer's post-commit ``cache.invalidate_for_brand`` hook is covered by:
# - ``tests/unit/test_composer.py`` — composer calls invalidate on successful
#   compose (composed_at set).
# - ``tests/unit/test_eligible_brands_cache.py`` — the invalidate path itself
#   (SCAN + DEL bounded by scope rows).
#
# An end-to-end integration test exercising composer → invalidate → fresh
# repo query requires straddling the test-body loop and TestClient portal
# loop with module-level redis/db state, which is inherently brittle in
# pytest-asyncio's per-test loop model. Skipping here in favor of the unit
# coverage; revisit if production behaviour diverges from what the units
# assert.
# ---------------------------------------------------------------------------
