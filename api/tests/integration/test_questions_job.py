# api/tests/integration/test_questions_job.py
import uuid

import pytest
import sqlalchemy as sa

from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.brand.model.profile import BrandProfile
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.questions.config import Config
from cortex_api.service.questions.job_service import QuestionsJobService
from cortex_api.service.questions.model.job import BrandWeeklyQuestions, QuestionJobStatus
from cortex_api.service.questions.model.question import WeeklyQuestion
from cortex_api.service.questions.repo.brand_questions_repo import BrandQuestionsRepo
from cortex_api.service.questions.repo.question_repo import QuestionRepo

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
        await QuestionRepo().upsert_all(s, [WeeklyQuestion(id="a", question_title="Q?", publisher_name="P", clicks=5)])

    async def fake_match(profile, snapshot, provider, question_count, min_relevance_score=40):
        return [
            {
                "id": "a",
                "text": "Q?",
                "media": "P",
                "asks": 5,
                "when": "",
                "intent": "Act",
                "score": 99,
                "competitorMentions": [],
            }
        ]

    svc = QuestionsJobService(
        db,
        BrandQuestionsRepo(),
        QuestionRepo(),
        Config(),
        BrandProfileRepo(),
        provider=object(),
        _match=fake_match,
    )
    await svc.start(bid)
    await svc.drain()
    done = await svc.get(bid)
    assert done.status == QuestionJobStatus.SUCCEEDED
    assert done.questions[0]["id"] == "a"

    again = await svc.start(bid)
    assert again.status == QuestionJobStatus.SUCCEEDED


async def test_empty_succeeded_row_is_regenerated():
    """A SUCCEEDED row with an empty questions list must NOT be deduped.

    Legacy rows were persisted SUCCEEDED-with-zero-questions during a transient
    bad state (empty snapshot pool + no category). The dedup in ``start`` froze
    them forever (regenerate=False always returned the empty row). A
    SUCCEEDED-but-empty result is not a real success — ``start`` must fall
    through and recompute so the stale empty result self-heals.
    """
    db = InfraContainer()._database_client_factory()
    bid = uuid.uuid4()
    async with db.session() as s:
        await s.execute(
            sa.text("insert into brand (id, display_name) values (:i,'T') on conflict do nothing"),
            {"i": str(bid)},
        )
        await BrandProfileRepo().upsert(s, BrandProfile(brand_id=bid, name="T"))

    jobs = BrandQuestionsRepo()
    # Seed the legacy bad state: SUCCEEDED with an empty questions list.
    async with db.session() as s:
        await jobs.create(s, BrandWeeklyQuestions(brand_id=bid))
        await jobs.mark_succeeded(s, bid, [])

    async def fake_match(profile, snapshot, provider, question_count, min_relevance_score=40):
        return [
            {
                "id": "x",
                "text": "real?",
                "media": "M",
                "asks": 1,
                "when": "",
                "intent": "Act",
                "score": 80,
                "competitorMentions": [],
            }
        ]

    svc = QuestionsJobService(
        db,
        jobs,
        QuestionRepo(),
        Config(),
        BrandProfileRepo(),
        provider=object(),
        _match=fake_match,
    )
    await svc.start(bid)
    await svc.drain()
    done = await svc.get(bid)
    assert done.status == QuestionJobStatus.SUCCEEDED
    assert len(done.questions) == 1  # regenerated, not the frozen empty list


async def test_succeeded_row_stale_vs_profile_is_regenerated():
    """A SUCCEEDED row generated BEFORE the profile's last update must regenerate.

    Re-onboarding the same brand_id with a different site re-extracts the
    profile (newer ``updated_at``) but the persisted weekly-questions row is the
    PREVIOUS profile's result. ``start`` must detect the profile is newer than
    the cached questions and recompute — otherwise the brand keeps showing the
    old brand's questions (the adidas-shows-mlytics bug).
    """
    db = InfraContainer()._database_client_factory()
    bid = uuid.uuid4()
    async with db.session() as s:
        await s.execute(
            sa.text("insert into brand (id, display_name) values (:i,'T') on conflict do nothing"),
            {"i": str(bid)},
        )
        await BrandProfileRepo().upsert(s, BrandProfile(brand_id=bid, name="Old Brand"))
        await QuestionRepo().upsert_all(s, [WeeklyQuestion(id="a", question_title="Q?", publisher_name="P", clicks=5)])

    calls = {"n": 0}

    async def fake_match(profile, snapshot, provider, question_count, min_relevance_score=40):
        calls["n"] += 1
        qid = "a" if calls["n"] == 1 else "b"
        return [
            {
                "id": qid,
                "text": "Q?",
                "media": "P",
                "asks": 5,
                "when": "",
                "intent": "Act",
                "score": 99,
                "competitorMentions": [],
            }
        ]

    svc = QuestionsJobService(
        db,
        BrandQuestionsRepo(),
        QuestionRepo(),
        Config(),
        BrandProfileRepo(),
        provider=object(),
        _match=fake_match,
    )

    # First generation: caches questions "a".
    await svc.start(bid)
    await svc.drain()
    first = await svc.get(bid)
    assert first.status == QuestionJobStatus.SUCCEEDED
    assert first.questions[0]["id"] == "a"

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
    assert done.status == QuestionJobStatus.SUCCEEDED
    assert done.questions[0]["id"] == "b", "stale-vs-profile row was not regenerated"
    assert calls["n"] == 2, "matcher should have run again for the re-extracted profile"


async def test_empty_matcher_output_marks_failed_not_succeeded():
    """The writer enforces the SUCCEEDED contract: an empty matcher result is a
    failure, never a SUCCEEDED-with-zero-questions row.

    This closes the loop on the dedup change — instead of persisting a degraded
    SUCCEEDED row (that ``start`` would then have to heal at read time), the
    worker routes empty matcher output to ``mark_failed`` so the bad state is
    never written. ``status=SUCCEEDED`` therefore always means non-empty.
    """
    db = InfraContainer()._database_client_factory()
    bid = uuid.uuid4()
    async with db.session() as s:
        await s.execute(
            sa.text("insert into brand (id, display_name) values (:i,'T') on conflict do nothing"),
            {"i": str(bid)},
        )
        await BrandProfileRepo().upsert(s, BrandProfile(brand_id=bid, name="T"))

    async def empty_match(profile, snapshot, provider, question_count, min_relevance_score=40):
        return []

    svc = QuestionsJobService(
        db,
        BrandQuestionsRepo(),
        QuestionRepo(),
        Config(),
        BrandProfileRepo(),
        provider=object(),
        _match=empty_match,
    )
    await svc.start(bid)
    await svc.drain()
    done = await svc.get(bid)
    assert done.status == QuestionJobStatus.FAILED
    assert done.questions == []
    assert done.error  # a descriptive failure reason, not a silent empty success
