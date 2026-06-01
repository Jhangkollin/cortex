# api/src/cortex_api/service/media_network/repo/member_repo.py
from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from cortex_api.service.media_network.model.member import MediaNetworkMember

# Columns to replace on conflict — everything except the primary key.
_REPLACE = ("member_name", "customer_uuid", "wau", "category_hint", "synced_at")


class MemberRepo:
    """CRUD on the `media_network_member` table."""

    async def list_all(self, session: AsyncSession) -> Sequence[MediaNetworkMember]:
        return (await session.exec(select(MediaNetworkMember))).all()

    async def upsert_all(self, session: AsyncSession, members: Sequence[MediaNetworkMember]) -> None:
        """Idempotent bulk upsert keyed on `hostname`.

        INSERT ... ON CONFLICT (hostname) DO UPDATE with wholesale-replace
        semantics for non-PK columns. `synced_at` is always stamped to now.
        """
        for m in members:
            values = m.model_dump()
            values["synced_at"] = datetime.utcnow()
            stmt = (
                pg_insert(MediaNetworkMember)
                .values(**values)
                .on_conflict_do_update(
                    index_elements=["hostname"],
                    set_={k: values[k] for k in _REPLACE},
                )
            )
            await session.execute(stmt)
        await session.flush()
