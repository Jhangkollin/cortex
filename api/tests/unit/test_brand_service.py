import pytest

from cortex_api.core.background import BackgroundTaskTracker
from cortex_api.core.exceptions import NotFoundError
from cortex_api.core.identifiers import uuid7
from cortex_api.service.brand.model.profile import BrandProfile
from cortex_api.service.brand.service import BrandService


class _FakeSessionCtx:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, *a):
        return False


class _FakeDB:
    def session(self):
        return _FakeSessionCtx()


class _FakeRepo:
    def __init__(self):
        self.store: dict = {}

    async def get(self, _session, brand_id):
        return self.store.get(brand_id)

    async def upsert(self, _session, profile):
        self.store[profile.brand_id] = profile
        return profile


class _NoopComposer:
    async def compose(self, _brand_id):
        return None


def _svc(repo):
    return BrandService(
        database_client=_FakeDB(),
        profile_repo=repo,
        config=object(),
        composer=_NoopComposer(),
        tracker=BackgroundTaskTracker(),
    )


async def test_get_profile_missing_raises_not_found() -> None:
    with pytest.raises(NotFoundError):
        await _svc(_FakeRepo()).get_profile(uuid7())


async def test_upsert_then_get_round_trips() -> None:
    repo = _FakeRepo()
    svc = _svc(repo)
    bid = uuid7()
    saved = await svc.upsert_profile(bid, BrandProfile(brand_id=bid, name="Svc Co"))
    assert saved.name == "Svc Co"
    got = await svc.get_profile(bid)
    assert got.brand_id == bid
    assert got.name == "Svc Co"


async def test_upsert_forces_tenant_brand_id() -> None:
    repo = _FakeRepo()
    svc = _svc(repo)
    tenant_bid = uuid7()
    other_bid = uuid7()
    body = BrandProfile(brand_id=other_bid, name="X")
    saved = await svc.upsert_profile(tenant_bid, body)
    assert saved.brand_id == tenant_bid
