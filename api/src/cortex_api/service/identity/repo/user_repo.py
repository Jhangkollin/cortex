"""AppUser persistence operations.

Repo is stateless — every method takes an `AsyncSession` per call. The
service that calls these methods owns the unit of work (when to commit,
when to roll back). This lets a single service method span multiple repos
transactionally (e.g. create brand + create admin membership in one TX).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from cortex_api.service.identity.model.app_user import AppUser


class UserRepo:
    """CRUD on the `app_user` table."""

    async def get_by_id(self, session: AsyncSession, user_id: UUID) -> AppUser | None:
        result = await session.exec(select(AppUser).where(AppUser.id == user_id))
        return result.first()

    async def get_by_oauth_subject(self, session: AsyncSession, oauth_subject: str) -> AppUser | None:
        result = await session.exec(select(AppUser).where(AppUser.oauth_subject == oauth_subject))
        return result.first()

    async def upsert(
        self,
        session: AsyncSession,
        oauth_subject: str,
        email: str,
        display_name: str | None,
    ) -> AppUser:
        """JIT-create or update by oauth_subject (called at OAuth login).

        Updates `email`, `display_name`, `last_login_at` on existing rows so
        Google profile changes (display name updates, address rotation) flow
        through without operator action.
        """
        existing = await self.get_by_oauth_subject(session, oauth_subject)
        now = datetime.utcnow()
        if existing is None:
            user = AppUser(
                oauth_subject=oauth_subject,
                email=email,
                display_name=display_name,
                last_login_at=now,
            )
            session.add(user)
            await session.flush()
            return user

        existing.email = email
        if display_name is not None:
            existing.display_name = display_name
        existing.last_login_at = now
        session.add(existing)
        await session.flush()
        return existing
