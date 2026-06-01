# api/tests/integration/test_questions_repos.py
import uuid

import pytest
import sqlalchemy as sa

from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.questions.model.job import BrandWeeklyQuestions, QuestionJobStatus
from cortex_api.service.questions.model.question import WeeklyQuestion
from cortex_api.service.questions.repo.brand_questions_repo import BrandQuestionsRepo
from cortex_api.service.questions.repo.question_repo import QuestionRepo

pytestmark = pytest.mark.integration


@pytest.fixture()
def db():
    return InfraContainer()._database_client_factory()


async def test_question_upsert_idempotent(db):
    repo = QuestionRepo()
    async with db.session() as s:
        await repo.upsert_all(s, [WeeklyQuestion(id="x1", question_title="Q?", publisher_name="P", clicks=10)])
    async with db.session() as s:
        await repo.upsert_all(s, [WeeklyQuestion(id="x1", question_title="Q?", publisher_name="P", clicks=20)])
    async with db.session() as s:
        rows = await repo.list_all(s)
    assert [(r.id, r.clicks) for r in rows if r.id == "x1"] == [("x1", 20)]


async def test_upsert_all_batches_writes(db):
    """upsert_all must batch the write, not issue one statement per row.

    The snapshot is ~200k rows; a per-row INSERT loop turns the sync into
    hundreds of thousands of sequential round-trips (the real cause of the
    multi-minute sync). This pins the batching contract: far fewer execute
    calls than rows.
    """
    repo = QuestionRepo()
    n = 250
    qs = [WeeklyQuestion(id=f"c{i}", question_title="Q", publisher_name="P", clicks=i) for i in range(n)]

    class _CountingSession:
        def __init__(self, inner):
            self._inner = inner
            self.execute_calls = 0

        async def execute(self, *a, **k):
            self.execute_calls += 1
            return await self._inner.execute(*a, **k)

        async def flush(self, *a, **k):
            return await self._inner.flush(*a, **k)

        def __getattr__(self, name):
            return getattr(self._inner, name)

    async with db.session() as s:
        counting = _CountingSession(s)
        await repo.upsert_all(counting, qs)
    assert counting.execute_calls >= 1
    assert counting.execute_calls < n  # batched, not one-per-row

    async with db.session() as s:
        rows = await repo.list_all(s)
    assert sum(1 for r in rows if r.id.startswith("c")) == n


async def test_upsert_all_multi_row_on_conflict_updates_each_row(db):
    """A batched ON CONFLICT DO UPDATE must update each conflicting row with
    ITS OWN proposed values (via EXCLUDED), across chunk boundaries — not a
    single shared value."""
    repo = QuestionRepo()
    n = 1500  # exceed the chunk size so multiple chunks run
    first = [WeeklyQuestion(id=f"d{i}", question_title="Q1", publisher_name="P1", clicks=i) for i in range(n)]
    async with db.session() as s:
        await repo.upsert_all(s, first)
    # Re-upsert the same ids with per-row-distinct new values in one call.
    second = [WeeklyQuestion(id=f"d{i}", question_title="Q2", publisher_name="P2", clicks=i + 10_000) for i in range(n)]
    async with db.session() as s:
        await repo.upsert_all(s, second)
    async with db.session() as s:
        rows = await repo.list_all(s)
    got = {r.id: (r.clicks, r.question_title) for r in rows if r.id.startswith("d")}
    assert len(got) == n  # updated in place, no duplicate rows
    assert got["d0"] == (10_000, "Q2")
    assert got["d1499"] == (11_499, "Q2")


async def test_brand_questions_in_flight_and_persist(db):
    repo = BrandQuestionsRepo()
    bid = uuid.uuid4()
    async with db.session() as s:
        await s.execute(
            sa.text("insert into brand (id, display_name) values (:i,'T') on conflict do nothing"), {"i": str(bid)}
        )
        await repo.create(s, BrandWeeklyQuestions(brand_id=bid))
    async with db.session() as s:
        assert (await repo.get(s, bid)) is not None
        assert (await repo.find_in_flight(s, bid)) is not None
    async with db.session() as s:
        await repo.mark_succeeded(s, bid, [{"id": "x1"}])
    async with db.session() as s:
        done = await repo.get(s, bid)
    assert done.status == QuestionJobStatus.SUCCEEDED and done.questions == [{"id": "x1"}]


async def test_brand_questions_create_resets_stale_row(db):
    repo = BrandQuestionsRepo()
    bid = uuid.uuid4()
    async with db.session() as s:
        await s.execute(
            sa.text("insert into brand (id, display_name) values (:i,'R') on conflict do nothing"), {"i": str(bid)}
        )
        await repo.create(s, BrandWeeklyQuestions(brand_id=bid))
    async with db.session() as s:
        await repo.mark_succeeded(s, bid, [{"id": "x1"}])
    async with db.session() as s:
        await repo.create(s, BrandWeeklyQuestions(brand_id=bid))
    async with db.session() as s:
        row = await repo.get(s, bid)
    assert row.status == QuestionJobStatus.PENDING
    assert row.error is None
    assert row.questions == []  # MUST be a list, not the string "[]"
