"""Database client — SQLModel + SQLAlchemy async session factory.

Sessions are short-lived and per-request. Repos receive an `AsyncSession`
through DI, not the engine itself.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession


class DatabaseClient:
    """Wraps the async engine + sessionmaker."""

    def __init__(
        self,
        url: str,
        pool_size: int = 10,
        pool_pre_ping: bool = True,
        echo: bool = False,
    ) -> None:
        self._logger = structlog.get_logger(__name__)
        self._engine = create_async_engine(
            url,
            pool_size=pool_size,
            pool_pre_ping=pool_pre_ping,
            echo=echo,
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self._logger.info("database_client_init", pool_size=pool_size)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Async context manager yielding a fresh session.

        Auto-rolls-back on exception, commits on clean exit.
        """
        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def dispose(self) -> None:
        """Close the engine pool. Call from app shutdown."""
        await self._engine.dispose()
