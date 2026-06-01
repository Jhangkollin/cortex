import asyncio

import pytest
from sqlalchemy import text

from cortex_api.core.identifiers import uuid7
from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.brand.model.profile import BrandProfile
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.brand_identity.model.brand import Brand

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
async def _schema():
    from sqlmodel import SQLModel

    db = InfraContainer()._database_client_factory()
    async with db.session() as s:
        conn = await s.connection()
        await conn.run_sync(SQLModel.metadata.create_all)


@pytest.fixture
def database_client():
    return InfraContainer()._database_client_factory()


async def test_upsert_inserts_then_get_returns(database_client) -> None:
    repo = BrandProfileRepo()
    bid = uuid7()
    async with database_client.session() as s:
        s.add(Brand(id=bid, display_name="RepoCo"))
        await s.flush()
        await repo.upsert(s, BrandProfile(brand_id=bid, name="RepoCo", region=["TW"]))

    async with database_client.session() as s:
        got = await repo.get(s, bid)
    assert got is not None
    assert got.name == "RepoCo"
    assert got.region == ["TW"]


async def test_upsert_replaces_existing(database_client) -> None:
    repo = BrandProfileRepo()
    bid = uuid7()
    async with database_client.session() as s:
        s.add(Brand(id=bid, display_name="RepoCo2"))
        await s.flush()
        await repo.upsert(s, BrandProfile(brand_id=bid, name="First", tagline="t1"))
    async with database_client.session() as s:
        await repo.upsert(s, BrandProfile(brand_id=bid, name="Second", products=[{"name": "P"}]))
    async with database_client.session() as s:
        got = await repo.get(s, bid)
    assert got is not None
    assert got.name == "Second"
    assert got.tagline is None
    assert got.products == [{"name": "P"}]


async def test_get_missing_returns_none(database_client) -> None:
    async with database_client.session() as s:
        assert await BrandProfileRepo().get(s, uuid7()) is None


async def test_concurrent_inserts_do_not_race(database_client) -> None:
    """Two concurrent first-time upserts for the same brand_id must both
    succeed atomically (last writer wins) — no unique-constraint 500.

    Reproduces the TOCTOU window deterministically: both transactions are
    held open and each completes its upsert call *before* the other
    commits, so a pre-write read in either would see an empty table. A
    read-modify-write implementation makes the second commit raise an
    IntegrityError on the brand_id PK; a native INSERT ... ON CONFLICT DO
    UPDATE is atomic, so both calls resolve cleanly to the same row.
    """
    repo = BrandProfileRepo()
    bid = uuid7()
    async with database_client.session() as s:
        s.add(Brand(id=bid, display_name="RaceCo"))
        await s.flush()

    # Deterministic interleave: A signals exactly when its row is written
    # (txn still open, PK lock held) and only then is B allowed to attempt
    # its own write. No wall-clock sleeps, so CI scheduler jitter can never
    # let B's INSERT precede A's lock acquisition and trivially pass.
    a_holds_lock = asyncio.Event()

    async def writer_a() -> None:
        async with database_client.session() as s:
            await repo.upsert(s, BrandProfile(brand_id=bid, name="A"))
            # Row written, transaction (and the PK row lock) still open.
            # Release B; it will enter its own upsert, observe an empty
            # table on a pre-write read, and block on this lock.
            a_holds_lock.set()
            # Stay in the transaction briefly so B reaches its blocking
            # INSERT before this commit releases the lock.
            await asyncio.sleep(0.3)

    async def writer_b() -> None:
        async with database_client.session() as s:
            # Fail fast instead of hanging CI if a regression reintroduces
            # a blocking read-then-write that waits on A's row lock.
            await s.exec(text("SET LOCAL statement_timeout = '5s'"))  # type: ignore[call-overload]
            # Proceed only once A's INSERT has landed and taken the lock.
            await a_holds_lock.wait()
            await repo.upsert(s, BrandProfile(brand_id=bid, name="B"))

    # With read-then-write, B's pre-write read sees no row, B's INSERT
    # blocks on A's uncommitted PK lock, then raises a unique-violation
    # IntegrityError once A commits. With INSERT ... ON CONFLICT DO UPDATE
    # the same lock-wait resolves into a clean update — no error. The outer
    # wait_for is a belt-and-braces guard so a regression can't hang CI.
    await asyncio.wait_for(asyncio.gather(writer_a(), writer_b()), timeout=15)

    async with database_client.session() as s:
        got = await repo.get(s, bid)
    assert got is not None
    assert got.name in ("A", "B")


async def test_upsert_replaces_every_non_identity_column(database_client) -> None:
    """A second upsert must reset *every* replaceable column, not just the
    hand-listed ones — proving the replace set is derived from the model.

    Guards against the Issue-2 drift class: a new column added to
    BrandProfile but forgotten in a hand-maintained replace list would
    silently never update after the first PUT.
    """
    repo = BrandProfileRepo()
    bid = uuid7()
    async with database_client.session() as s:
        s.add(Brand(id=bid, display_name="DriftCo"))
        await s.flush()
        await repo.upsert(
            s,
            BrandProfile(
                brand_id=bid,
                name="First",
                legal_name="First Legal Inc",
                tagline="t1",
                monogram="FL",
                brand_color="#fff",
                founded="1999",
                about="about-1",
                source_url="https://first.example",
                industry_vertical="fintech",
                primary_jurisdiction="TW",
                category_value="cards",
                category_confidence=90,
                category_alternatives=["loans"],
                region=["TW"],
                voice_samples=[{"q": "1"}],
                products=[{"name": "P1"}],
                competitors=[{"name": "C1"}],
                media_matches=[{"url": "m1"}],
                extraction_meta={"extracted_at": "2026-01-01T00:00:00Z"},
            ),
        )
    async with database_client.session() as s:
        await repo.upsert(s, BrandProfile(brand_id=bid, name="Second"))
    async with database_client.session() as s:
        got = await repo.get(s, bid)

    assert got is not None
    assert got.name == "Second"
    assert got.legal_name is None
    assert got.tagline is None
    assert got.monogram is None
    assert got.brand_color is None
    assert got.founded is None
    assert got.about is None
    assert got.source_url is None
    assert got.industry_vertical is None
    assert got.primary_jurisdiction is None
    assert got.category_value is None
    assert got.category_confidence is None
    assert got.category_alternatives == []
    assert got.region == []
    assert got.voice_samples == []
    assert got.products == []
    assert got.competitors == []
    assert got.media_matches == []
    assert got.extraction_meta is None
