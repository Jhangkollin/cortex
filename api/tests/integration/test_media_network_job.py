# api/tests/integration/test_media_network_job.py
import uuid

import pytest
import sqlalchemy as sa

from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.brand.model.profile import BrandProfile
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.media_network.config import Config
from cortex_api.service.media_network.job_service import MediaNetworkJobService
from cortex_api.service.media_network.model.job import MediaJobStatus
from cortex_api.service.media_network.model.member import MediaNetworkMember
from cortex_api.service.media_network.repo.brand_media_repo import BrandMediaRepo
from cortex_api.service.media_network.repo.member_repo import MemberRepo

pytestmark = pytest.mark.integration


async def test_job_succeeds_and_persists():
    db = InfraContainer()._database_client_factory()
    bid = uuid.uuid4()
    async with db.session() as s:
        await s.execute(
            sa.text("insert into brand (id, display_name) values (:i,'T') on conflict do nothing"), {"i": str(bid)}
        )
        await BrandProfileRepo().upsert(s, BrandProfile(brand_id=bid, name="T"))
        await MemberRepo().upsert_all(s, [MediaNetworkMember(hostname="a.tw", member_name="A", wau=5)])

    async def fake_match(profile, catalog, provider, outlet_count):
        return [
            {
                "hostname": "a.tw",
                "member_name": "A",
                "wau": 5,
                "relevance": 99,
                "why": "w",
                "topics": [],
                "context_agent_label": "L",
                "audience_descriptor": "A",
            }
        ]

    svc = MediaNetworkJobService(
        db,
        BrandMediaRepo(),
        MemberRepo(),
        Config(),
        brand_profile_repo=BrandProfileRepo(),
        provider=object(),
        _match=fake_match,
    )
    await svc.start(bid)
    await svc.drain()
    done = await svc.get(bid)
    assert done.status == MediaJobStatus.SUCCEEDED
    assert done.outlets[0]["hostname"] == "a.tw"

    again = await svc.start(bid)
    assert again.status == MediaJobStatus.SUCCEEDED


async def test_succeeded_row_stale_vs_profile_is_regenerated():
    """A SUCCEEDED media row generated BEFORE the profile's last update must regenerate.

    Re-onboarding the same brand_id with a different site re-extracts the
    profile (newer ``updated_at``) but the persisted brand_media_network row is
    the PREVIOUS profile's outlets. ``start`` must detect the profile is newer
    than the cached media and recompute — otherwise the brand keeps showing the
    previous brand's media network (the same class of bug fixed for weekly
    questions in cortex#70).
    """
    db = InfraContainer()._database_client_factory()
    bid = uuid.uuid4()
    async with db.session() as s:
        await s.execute(
            sa.text("insert into brand (id, display_name) values (:i,'T') on conflict do nothing"), {"i": str(bid)}
        )
        await BrandProfileRepo().upsert(s, BrandProfile(brand_id=bid, name="Old Brand"))
        await MemberRepo().upsert_all(s, [MediaNetworkMember(hostname="a.tw", member_name="A", wau=5)])

    calls = {"n": 0}

    async def fake_match(profile, catalog, provider, outlet_count):
        calls["n"] += 1
        host = "a.tw" if calls["n"] == 1 else "b.tw"
        return [
            {
                "hostname": host,
                "member_name": "A",
                "wau": 5,
                "relevance": 99,
                "why": "w",
                "topics": [],
                "context_agent_label": "L",
                "audience_descriptor": "A",
            }
        ]

    svc = MediaNetworkJobService(
        db,
        BrandMediaRepo(),
        MemberRepo(),
        Config(),
        brand_profile_repo=BrandProfileRepo(),
        provider=object(),
        _match=fake_match,
    )

    # First generation: caches outlet "a.tw".
    await svc.start(bid)
    await svc.drain()
    first = await svc.get(bid)
    assert first.status == MediaJobStatus.SUCCEEDED
    assert first.outlets[0]["hostname"] == "a.tw"

    # Re-onboard: bump the profile's updated_at strictly past the cached row.
    async with db.session() as s:
        await s.execute(
            sa.text("update brand_profile set updated_at = now() + interval '1 second' where brand_id = :i"),
            {"i": str(bid)},
        )

    # start() must now treat the cached row as stale-vs-profile and regenerate.
    await svc.start(bid)
    await svc.drain()
    done = await svc.get(bid)
    assert done.outlets[0]["hostname"] == "b.tw", "stale-vs-profile media was not regenerated"
    assert calls["n"] == 2, "matcher should have run again for the re-extracted profile"
