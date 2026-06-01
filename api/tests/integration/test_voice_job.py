import uuid

import pytest
import sqlalchemy as sa

from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.brand.model.profile import BrandProfile
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.voice.config import Config
from cortex_api.service.voice.job_service import VoiceJobService
from cortex_api.service.voice.model.job import VoiceJobStatus
from cortex_api.service.voice.repo.brand_voice_repo import BrandVoiceRepo

pytestmark = pytest.mark.integration


async def test_job_succeeds_and_persists():
    db = InfraContainer()._database_client_factory()
    bid = uuid.uuid4()
    async with db.session() as s:
        await s.execute(
            sa.text("insert into brand (id, display_name) values (:i,'T') on conflict do nothing"),
            {"i": str(bid)},
        )
        await BrandProfileRepo().upsert(s, BrandProfile(brand_id=bid, name="T"))

    async def fake_generate(profile, provider, styles=("expert", "warm", "playful")):
        return {"expert": "E", "warm": "W", "playful": "P"}

    svc = VoiceJobService(
        db,
        BrandVoiceRepo(),
        Config(),
        BrandProfileRepo(),
        provider=object(),
        _generate=fake_generate,
    )
    await svc.start(bid)
    await svc.drain()
    done = await svc.get(bid)
    assert done.status == VoiceJobStatus.SUCCEEDED
    assert done.samples == {"expert": "E", "warm": "W", "playful": "P"}
    again = await svc.start(bid)
    assert again.status == VoiceJobStatus.SUCCEEDED


async def test_succeeded_row_stale_vs_profile_is_regenerated():
    """A SUCCEEDED voice row generated BEFORE the profile's last update must regenerate.

    Re-onboarding the same brand_id with a different site re-extracts the
    profile (newer ``updated_at``) but the persisted brand_voice row is the
    PREVIOUS profile's samples. ``start`` must detect the profile is newer than
    the cached voice and recompute — otherwise the brand keeps showing the
    previous brand's voice preview (the same class of bug fixed for weekly
    questions in cortex#70).
    """
    db = InfraContainer()._database_client_factory()
    bid = uuid.uuid4()
    async with db.session() as s:
        await s.execute(
            sa.text("insert into brand (id, display_name) values (:i,'T') on conflict do nothing"),
            {"i": str(bid)},
        )
        await BrandProfileRepo().upsert(s, BrandProfile(brand_id=bid, name="Old Brand"))

    calls = {"n": 0}

    async def fake_generate(profile, provider, styles=("expert", "warm", "playful")):
        calls["n"] += 1
        token = "old" if calls["n"] == 1 else "new"
        return {"expert": token, "warm": token, "playful": token}

    svc = VoiceJobService(
        db,
        BrandVoiceRepo(),
        Config(),
        BrandProfileRepo(),
        provider=object(),
        _generate=fake_generate,
    )

    # First generation: caches the "old" samples.
    await svc.start(bid)
    await svc.drain()
    first = await svc.get(bid)
    assert first.status == VoiceJobStatus.SUCCEEDED
    assert first.samples == {"expert": "old", "warm": "old", "playful": "old"}

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
    assert done.samples == {"expert": "new", "warm": "new", "playful": "new"}, (
        "stale-vs-profile voice was not regenerated"
    )
    assert calls["n"] == 2, "generator should have run again for the re-extracted profile"
