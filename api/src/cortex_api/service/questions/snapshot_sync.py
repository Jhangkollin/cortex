# api/src/cortex_api/service/questions/snapshot_sync.py
from __future__ import annotations

import hashlib
import re
from datetime import date

import structlog

from cortex_api.core.exceptions import BadRequestError
from cortex_api.infra.database_client import DatabaseClient
from cortex_api.infra.databricks_client import DatabricksClient
from cortex_api.service.questions.model.question import WeeklyQuestion
from cortex_api.service.questions.repo.question_repo import QuestionRepo

_logger = structlog.get_logger(__name__)

_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _qid(title: str, publisher: str) -> str:
    return hashlib.sha256(f"{title}|{publisher}".encode()).hexdigest()[:64]


def _coerce_date(value: object) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


async def sync_snapshot(
    dbx: DatabricksClient,
    db: DatabaseClient,
    questions: QuestionRepo,
    catalog_catalog: str,
) -> int:
    """Pull real weekly reader-question engagement and upsert the snapshot.

    Raises on Databricks failure WITHOUT upserting (prior snapshot intact).
    """
    if not _IDENTIFIER_RE.fullmatch(catalog_catalog):
        raise BadRequestError(f"dbx_catalog {catalog_catalog!r} is not a valid SQL identifier")
    rows = await dbx.fetch_all(
        f"select question_title, publisher_name, measure(question_clicks) as clicks, "
        f"max(event_date) as last_event_date "
        f"from {catalog_catalog}.aigc_metrics.aigc_clickstream_metrics "
        f"where event_date >= dateadd(day,-7,"
        f"(select max(event_date) from {catalog_catalog}.aigc_metrics.aigc_clickstream_metrics)) "
        f"and question_title is not null and question_title <> '' "
        f"group by question_title, publisher_name order by clicks desc"
    )
    items: list[WeeklyQuestion] = []
    for r in rows:
        title, pub = str(r[0]), str(r[1])
        items.append(
            WeeklyQuestion(
                id=_qid(title, pub),
                question_title=title[:2048],
                publisher_name=pub[:255],
                clicks=int(r[2]) if r[2] is not None else 0,
                last_event_date=_coerce_date(r[3]) if len(r) > 3 else None,
            )
        )
    if items:
        async with db.session() as session:
            await questions.upsert_all(session, items)
    _logger.info("weekly_questions_synced", questions=len(items))
    return len(items)
