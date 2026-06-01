# api/tests/integration/test_media_repos.py
import uuid

import pytest
import sqlalchemy as sa

from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.media_network.model.job import BrandMediaNetwork, MediaJobStatus
from cortex_api.service.media_network.model.member import MediaNetworkMember
from cortex_api.service.media_network.repo.brand_media_repo import BrandMediaRepo
from cortex_api.service.media_network.repo.member_repo import MemberRepo

pytestmark = pytest.mark.integration


@pytest.fixture()
def db():
    return InfraContainer()._database_client_factory()


async def test_member_upsert_idempotent(db):
    repo = MemberRepo()
    async with db.session() as s:
        await repo.upsert_all(s, [MediaNetworkMember(hostname="h1", member_name="A", wau=10)])
    async with db.session() as s:
        await repo.upsert_all(s, [MediaNetworkMember(hostname="h1", member_name="A", wau=20)])
    async with db.session() as s:
        rows = await repo.list_all(s)
    assert [(r.hostname, r.wau) for r in rows if r.hostname == "h1"] == [("h1", 20)]


async def test_brand_media_in_flight_and_persist(db):
    repo = BrandMediaRepo()
    bid = uuid.uuid4()
    async with db.session() as s:
        await s.execute(
            sa.text("insert into brand (id, display_name) values (:i, 'T') on conflict do nothing"), {"i": str(bid)}
        )
        await repo.create(s, BrandMediaNetwork(brand_id=bid))
    async with db.session() as s:
        assert (await repo.get(s, bid)) is not None
        assert (await repo.find_in_flight(s, bid)) is not None
    async with db.session() as s:
        await repo.mark_succeeded(s, bid, [{"hostname": "h1"}])
    async with db.session() as s:
        done = await repo.get(s, bid)
    assert done.status == MediaJobStatus.SUCCEEDED and done.outlets == [{"hostname": "h1"}]


async def test_brand_media_create_resets_stale_row(db):
    """create() on a SUCCEEDED row resets status->PENDING, error->None, outlets->[]."""
    repo = BrandMediaRepo()
    bid = uuid.uuid4()
    async with db.session() as s:
        await s.execute(
            sa.text("insert into brand (id, display_name) values (:i, 'R') on conflict do nothing"), {"i": str(bid)}
        )
        await repo.create(s, BrandMediaNetwork(brand_id=bid))
    async with db.session() as s:
        await repo.mark_succeeded(s, bid, [{"hostname": "h1"}])
    async with db.session() as s:
        await repo.create(s, BrandMediaNetwork(brand_id=bid))
    async with db.session() as s:
        row = await repo.get(s, bid)
    assert row.status == MediaJobStatus.PENDING
    assert row.error is None
    assert row.outlets == []  # must be a list, not the string "[]"
