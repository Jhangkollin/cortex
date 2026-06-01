# api/tests/unit/test_media_snapshot_sync.py
import contextlib

import pytest

from cortex_api.core.exceptions import BadRequestError, UpstreamError
from cortex_api.service.media_network.snapshot_sync import sync_snapshot


class FakeDbx:
    def __init__(self, by_sql):
        self._m = by_sql

    async def fetch_all(self, sql, params=None):
        for k, v in self._m.items():
            if k in sql:
                if isinstance(v, Exception):
                    raise v
                return v
        return []


class FakeMemberRepo:
    def __init__(self):
        self.upserted = None

    async def upsert_all(self, session, members):
        self.upserted = list(members)


class FakeDB:
    def session(self):
        @contextlib.asynccontextmanager
        async def _s():
            yield object()

        return _s()


async def test_maps_catalog_and_wau():
    dbx = FakeDbx(
        {
            "member_sheet_registry": [["CMoney", "u1", "aigc.cmoney.tw"]],
            "aigc_clickstream_metrics": [["CMoney", 117260]],
        }
    )
    repo = FakeMemberRepo()
    n = await sync_snapshot(dbx, FakeDB(), repo, catalog_catalog="aigc_prod")
    assert n == 1
    m = repo.upserted[0]
    assert m.hostname == "aigc.cmoney.tw" and m.member_name == "CMoney" and m.wau == 117260


async def test_query_failure_does_not_upsert():
    dbx = FakeDbx({"member_sheet_registry": UpstreamError("dbx down")})
    repo = FakeMemberRepo()
    with pytest.raises(UpstreamError):
        await sync_snapshot(dbx, FakeDB(), repo, catalog_catalog="aigc_prod")
    assert repo.upserted is None


@pytest.mark.parametrize(
    "bad_catalog",
    [
        "a; drop",
        "a; DROP TABLE brand--",
        "aigc prod",
        "aigc-prod",
        "1starts_with_digit",
        "",
        "a.b",
    ],
)
async def test_invalid_catalog_raises_before_fetch(bad_catalog: str):
    """An invalid SQL identifier is rejected before any Databricks fetch."""
    dbx = FakeDbx({})
    repo = FakeMemberRepo()
    with pytest.raises(BadRequestError, match="valid SQL identifier"):
        await sync_snapshot(dbx, FakeDB(), repo, catalog_catalog=bad_catalog)
    assert repo.upserted is None
