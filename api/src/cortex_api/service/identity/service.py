"""UserService — OAuth recognize + AppUser lifecycle.

Brand-side and publisher-side identity live in `service/brand_identity/` and
`service/publisher_identity/` respectively. This shared identity context owns
only the AppUser entity and the OAuth recognition flow.
"""

from __future__ import annotations

from uuid import UUID

import structlog

from cortex_api.core.exceptions import NotFoundError
from cortex_api.infra.database_client import DatabaseClient
from cortex_api.service.identity.config import Config
from cortex_api.service.identity.model.app_user import AppUser
from cortex_api.service.identity.repo.user_repo import UserRepo


class UserService:
    """OAuth-driven AppUser lifecycle."""

    def __init__(
        self,
        database_client: DatabaseClient,
        user_repo: UserRepo,
        config: Config,
    ) -> None:
        self._logger = structlog.get_logger(__name__)
        self._db = database_client
        self._user_repo = user_repo
        self._config = config

    async def recognize_user(
        self,
        oauth_subject: str,
        email: str,
        display_name: str | None = None,
    ) -> AppUser:
        """Called at OAuth callback. Upserts the AppUser row and returns it."""
        async with self._db.session() as session:
            user = await self._user_repo.upsert(
                session,
                oauth_subject=oauth_subject,
                email=email,
                display_name=display_name,
            )
            self._logger.info(
                "user_recognized",
                user_id=str(user.id),
                oauth_subject=oauth_subject,
                created=user.created_at == user.last_login_at,
            )
            return user

    async def get_user(self, user_id: UUID) -> AppUser:
        """Fetch by primary key. Raises NotFoundError if absent."""
        async with self._db.session() as session:
            user = await self._user_repo.get_by_id(session, user_id)
            if user is None:
                raise NotFoundError(f"user {user_id} not found")
            return user
