# api/tests/unit/test_questions_snapshot_sync.py
import contextlib

import pytest

from cortex_api.core.exceptions import BadRequestError, UpstreamError
from cortex_api.service.questions.snapshot_sync import sync_snapshot


class FakeDbx:
    def __init__(self, rows):
        self._rows = rows

    async def fetch_all(self, sql, params=None):
        if isinstance(self._rows, Exception):
            raise self._rows
        return self._rows


class FakeRepo:
    def __init__(self):
        self.upserted = None

    async def upsert_all(self, session, items):
        self.upserted = list(items)


class FakeDB:
    def session(self):
        @contextlib.asynccontextmanager
        async def _s():
            yield object()

        return _s()


async def test_maps_rows():
    dbx = FakeDbx([["Best ETF?", "CMoney", 300, "2026-05-15"]])
    repo = FakeRepo()
    n = await sync_snapshot(dbx, FakeDB(), repo, catalog_catalog="aigc_prod")
    assert n == 1
    q = repo.upserted[0]
    assert q.question_title == "Best ETF?" and q.publisher_name == "CMoney" and q.clicks == 300
    assert q.id and len(q.id) <= 64


async def test_query_failure_does_not_upsert():
    repo = FakeRepo()
    with pytest.raises(UpstreamError):
        await sync_snapshot(FakeDbx(UpstreamError("dbx down")), FakeDB(), repo, catalog_catalog="aigc_prod")
    assert repo.upserted is None


async def test_invalid_catalog_raises_before_fetch():
    repo = FakeRepo()
    with pytest.raises(BadRequestError):
        await sync_snapshot(FakeDbx([]), FakeDB(), repo, catalog_catalog="a; drop")
    assert repo.upserted is None
