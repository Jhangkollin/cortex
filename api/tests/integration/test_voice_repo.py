import uuid

import pytest
import sqlalchemy as sa

from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.voice.model.job import BrandVoice, VoiceJobStatus
from cortex_api.service.voice.repo.brand_voice_repo import BrandVoiceRepo

pytestmark = pytest.mark.integration


@pytest.fixture()
def db():
    return InfraContainer()._database_client_factory()


async def test_in_flight_and_persist(db):
    repo = BrandVoiceRepo()
    bid = uuid.uuid4()
    async with db.session() as s:
        await s.execute(
            sa.text("insert into brand (id, display_name) values (:i,'T') on conflict do nothing"), {"i": str(bid)}
        )
        await repo.create(s, BrandVoice(brand_id=bid))
    async with db.session() as s:
        assert (await repo.get(s, bid)) is not None
        assert (await repo.find_in_flight(s, bid)) is not None
    async with db.session() as s:
        await repo.mark_succeeded(s, bid, {"expert": "E", "warm": "W", "playful": "P"})
    async with db.session() as s:
        done = await repo.get(s, bid)
    assert done.status == VoiceJobStatus.SUCCEEDED and done.samples == {"expert": "E", "warm": "W", "playful": "P"}


async def test_create_resets_stale_row(db):
    repo = BrandVoiceRepo()
    bid = uuid.uuid4()
    async with db.session() as s:
        await s.execute(
            sa.text("insert into brand (id, display_name) values (:i,'R') on conflict do nothing"), {"i": str(bid)}
        )
        await repo.create(s, BrandVoice(brand_id=bid))
    async with db.session() as s:
        await repo.mark_succeeded(s, bid, {"expert": "X"})
    async with db.session() as s:
        await repo.create(s, BrandVoice(brand_id=bid))
    async with db.session() as s:
        row = await repo.get(s, bid)
    assert row.status == VoiceJobStatus.PENDING
    assert row.error is None
    assert row.samples == {}  # MUST be a dict, not the string "{}"
