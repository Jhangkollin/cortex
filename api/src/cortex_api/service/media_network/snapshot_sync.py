# api/src/cortex_api/service/media_network/snapshot_sync.py
from __future__ import annotations

import re

import structlog

from cortex_api.core.exceptions import BadRequestError
from cortex_api.infra.database_client import DatabaseClient
from cortex_api.infra.databricks_client import DatabricksClient
from cortex_api.service.media_network.model.member import MediaNetworkMember
from cortex_api.service.media_network.repo.member_repo import MemberRepo

_logger = structlog.get_logger(__name__)

_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


async def sync_snapshot(
    dbx: DatabricksClient,
    db: DatabaseClient,
    members: MemberRepo,
    catalog_catalog: str,
) -> int:
    """Pull the real publisher catalog + per-outlet WAU and upsert the snapshot.

    Raises on Databricks failure WITHOUT upserting, so a failed sync leaves
    the prior snapshot intact (onboarding keeps working off the last sync/seed).
    """
    if not _IDENTIFIER_RE.fullmatch(catalog_catalog):
        raise BadRequestError(f"dbx_catalog {catalog_catalog!r} is not a valid SQL identifier")
    registry = await dbx.fetch_all(
        f"select member_name, customer_uuid, hostname from {catalog_catalog}.reports.member_sheet_registry"
    )
    wau_rows = await dbx.fetch_all(
        f"select publisher_name, measure(unique_visitors) as wau "
        f"from {catalog_catalog}.aigc_metrics.aigc_clickstream_metrics "
        f"where event_date >= dateadd(day,-7,"
        f"(select max(event_date) from {catalog_catalog}.aigc_metrics.aigc_clickstream_metrics)) "
        f"group by publisher_name"
    )
    wau_by_name: dict[str, int] = {
        str(r[0]): int(r[1]) for r in wau_rows if r and r[0] is not None and r[1] is not None
    }
    rows: list[MediaNetworkMember] = []
    for r in registry:
        name, cust, host = str(r[0]), (str(r[1]) if r[1] else None), str(r[2])
        rows.append(
            MediaNetworkMember(
                hostname=host,
                member_name=name,
                customer_uuid=cust,
                wau=wau_by_name.get(name),
                category_hint=None,
            )
        )
    if rows:
        async with db.session() as session:
            await members.upsert_all(session, rows)
    _logger.info("media_snapshot_synced", members=len(rows))
    return len(rows)
