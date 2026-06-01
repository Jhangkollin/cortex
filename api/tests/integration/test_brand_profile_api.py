import contextlib

import pytest
from fastapi.testclient import TestClient

from cortex_api.app.dependencies.auth import authenticated_user
from cortex_api.core.identifiers import uuid7
from cortex_api.infra.container import Container as InfraContainer
from cortex_api.main import create_app
from cortex_api.service.brand_identity.model.brand import Brand
from cortex_api.service.identity.model.authed_user import AuthedUser

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
async def _schema():
    from sqlmodel import SQLModel

    db = InfraContainer()._database_client_factory()
    async with db.session() as s:
        conn = await s.connection()
        await conn.run_sync(SQLModel.metadata.create_all)


def _authed(brand_id, caps):
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
        s.add(Brand(id=bid, display_name="ApiCo"))
        await s.flush()
    return bid


@contextlib.contextmanager
def _client(brand_id, caps, *, jwt_brand_id=None):
    """TestClient whose JWT carries `jwt_brand_id` (defaults to `brand_id`).

    Splitting the JWT's brand from the URL's brand lets a test prove the
    cross-tenant rejection path: a token scoped to brand A hitting a brand
    B URL must be refused by `active_brand`, never served B's data.
    """
    app = create_app()
    token_brand = jwt_brand_id if jwt_brand_id is not None else brand_id
    app.dependency_overrides[authenticated_user] = lambda: _authed(token_brand, caps)
    with TestClient(app) as c:
        yield c


async def test_get_missing_profile_404(brand_id) -> None:
    with _client(brand_id, ["view_brand_dashboard"]) as c:
        assert c.get(f"/v1/brand/{brand_id}/profile").status_code == 404


async def test_put_then_get_round_trip(brand_id) -> None:
    with _client(brand_id, ["view_brand_dashboard", "edit_brand_settings"]) as c:
        put = c.put(
            f"/v1/brand/{brand_id}/profile",
            json={"name": "ApiCo", "region": ["TW"], "products": [{"name": "Card", "category": "Credit"}]},
        )
        assert put.status_code == 200, put.text
        assert put.json()["name"] == "ApiCo"
        got = c.get(f"/v1/brand/{brand_id}/profile")
        assert got.status_code == 200
        body = got.json()
        assert body["region"] == ["TW"]
        assert body["products"][0]["name"] == "Card"


async def test_put_without_capability_403(brand_id) -> None:
    with _client(brand_id, ["view_brand_dashboard"]) as c:
        assert c.put(f"/v1/brand/{brand_id}/profile", json={"name": "X"}).status_code == 403


@pytest.fixture
async def other_brand_with_profile():
    """A second brand (brand B) that already has a stored profile.

    Used to assert a cross-tenant caller can neither read nor overwrite
    B's row — and crucially never *sees* B's data in the response body.
    """
    from cortex_api.service.brand.model.profile import BrandProfile

    bid = uuid7()
    db = InfraContainer()._database_client_factory()
    async with db.session() as s:
        s.add(Brand(id=bid, display_name="VictimCo"))
        await s.flush()
        s.add(BrandProfile(brand_id=bid, name="VictimCo Secret Profile"))
    return bid


async def test_put_cross_tenant_rejected(brand_id, other_brand_with_profile) -> None:
    """JWT scoped to brand A may not write brand B's profile.

    `active_brand` raises `ContextMismatchError` when the URL `brand_id`
    does not match the JWT `active_context.id`. Per
    `app/exception_handlers.py` that maps to HTTP 400 (a deliberate "your
    request is malformed for this token" signal, not a 403 — the caller
    is authenticated, the *request* is incoherent). The security-critical
    assertions are the negatives: NOT 200, and brand B's row untouched.
    """
    with _client(other_brand_with_profile, ["view_brand_dashboard", "edit_brand_settings"], jwt_brand_id=brand_id) as c:
        resp = c.put(
            f"/v1/brand/{other_brand_with_profile}/profile",
            json={"name": "Attacker Overwrite"},
        )

    assert resp.status_code != 200
    assert 400 <= resp.status_code < 500, f"expected a 4xx client rejection, got {resp.status_code}: {resp.text}"
    assert "VictimCo Secret Profile" not in resp.text
    assert "Attacker Overwrite" not in resp.text

    # Brand B's profile must be exactly as seeded — not overwritten.
    db = InfraContainer()._database_client_factory()
    from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo

    async with db.session() as s:
        victim = await BrandProfileRepo().get(s, other_brand_with_profile)
    assert victim is not None
    assert victim.name == "VictimCo Secret Profile"


async def test_get_cross_tenant_does_not_leak(brand_id, other_brand_with_profile) -> None:
    """JWT scoped to brand A may not read brand B's profile.

    The most security-sensitive read path: a 4xx must be returned and
    brand B's stored data must never appear in the response.
    """
    with _client(other_brand_with_profile, ["view_brand_dashboard"], jwt_brand_id=brand_id) as c:
        resp = c.get(f"/v1/brand/{other_brand_with_profile}/profile")

    assert resp.status_code != 200
    assert 400 <= resp.status_code < 500, f"expected a 4xx client rejection, got {resp.status_code}: {resp.text}"
    assert "VictimCo Secret Profile" not in resp.text


@pytest.fixture
def brand_admin_client(brand_id):
    """TestClient whose JWT carries ADMIN capabilities (view + edit)."""
    with _client(brand_id, ["view_brand_dashboard", "edit_brand_settings", "manage_brand_users"]) as c:
        yield c


@pytest.fixture
def brand_viewer_client(brand_id):
    """TestClient whose JWT carries only VIEW_BRAND_DASHBOARD (no edit)."""
    with _client(brand_id, ["view_brand_dashboard"]) as c:
        yield c


async def test_onboarding_status_false_then_true(brand_admin_client, brand_id):
    r = brand_admin_client.get(f"/v1/brand/{brand_id}/onboarding/status")
    assert r.status_code == 200
    assert r.json() == {"onboarded": False}
    c = brand_admin_client.post(f"/v1/brand/{brand_id}/onboarding/complete")
    assert c.status_code == 200
    assert "onboarded_at" in c.json()
    r2 = brand_admin_client.get(f"/v1/brand/{brand_id}/onboarding/status")
    assert r2.status_code == 200
    assert r2.json() == {"onboarded": True}


async def test_onboarding_complete_is_idempotent(brand_admin_client, brand_id):
    first = brand_admin_client.post(f"/v1/brand/{brand_id}/onboarding/complete")
    second = brand_admin_client.post(f"/v1/brand/{brand_id}/onboarding/complete")
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["onboarded_at"] == second.json()["onboarded_at"]


async def test_onboarding_complete_forbidden_without_edit_cap(brand_viewer_client, brand_id):
    r = brand_viewer_client.post(f"/v1/brand/{brand_id}/onboarding/complete")
    assert r.status_code == 403


async def test_put_body_brand_id_cannot_target_another_tenant(brand_id) -> None:
    """Second line of defense: even a same-tenant PUT whose *body* carries
    a foreign `brand_id` must persist under the JWT's brand, not the body's.

    `BrandService.upsert_profile` reassigns `profile.brand_id` to the
    tenant id, so a malformed/hostile body can never write another
    brand's row. This proves that override is live, not dead code.
    """
    foreign = uuid7()
    with _client(brand_id, ["view_brand_dashboard", "edit_brand_settings"]) as c:
        put = c.put(
            f"/v1/brand/{brand_id}/profile",
            json={"name": "Legit", "brand_id": str(foreign)},
        )
        assert put.status_code == 200, put.text
        got = c.get(f"/v1/brand/{brand_id}/profile")
        assert got.status_code == 200

    db = InfraContainer()._database_client_factory()
    from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo

    async with db.session() as s:
        # Row landed on the JWT tenant, NOT the body-supplied foreign id.
        assert await BrandProfileRepo().get(s, foreign) is None
        mine = await BrandProfileRepo().get(s, brand_id)
    assert mine is not None
    assert mine.name == "Legit"
