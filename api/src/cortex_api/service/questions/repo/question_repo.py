# api/src/cortex_api/service/questions/repo/question_repo.py
from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from cortex_api.service.questions.model.question import WeeklyQuestion

# Columns to replace on conflict — everything except the primary key.
_REPLACE = ("question_title", "publisher_name", "clicks", "last_event_date", "synced_at")

# Rows per INSERT statement. The snapshot is ~200k rows; one statement per row
# means ~200k sequential round-trips (minutes). Batching collapses that to
# ceil(N / chunk) statements. 1000 rows x 6 cols = 6000 bind params, far under
# Postgres's 65535-parameter cap, with comfortable headroom for new columns.
_UPSERT_CHUNK_SIZE = 1000


class QuestionRepo:
    """CRUD on the `weekly_question` table."""

    async def list_all(self, session: AsyncSession) -> Sequence[WeeklyQuestion]:
        return (await session.exec(select(WeeklyQuestion))).all()

    async def upsert_all(self, session: AsyncSession, questions: Sequence[WeeklyQuestion]) -> None:
        """Idempotent bulk upsert keyed on `id`.

        Multi-row INSERT ... ON CONFLICT (id) DO UPDATE, chunked. Non-PK columns
        are replaced from the proposed row via ``excluded`` (so each conflicting
        row updates to ITS OWN new values, not a shared one). ``synced_at`` is
        stamped to now for every row. Batched into ``_UPSERT_CHUNK_SIZE`` rows
        per statement — one statement per row turned the ~200k-row sync into
        hundreds of thousands of round-trips.
        """
        now = datetime.utcnow()
        rows = [{**q.model_dump(), "synced_at": now} for q in questions]
        for start in range(0, len(rows), _UPSERT_CHUNK_SIZE):
            chunk = rows[start : start + _UPSERT_CHUNK_SIZE]
            stmt = pg_insert(WeeklyQuestion).values(chunk)
            stmt = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={k: stmt.excluded[k] for k in _REPLACE},
            )
            await session.execute(stmt)
        await session.flush()
