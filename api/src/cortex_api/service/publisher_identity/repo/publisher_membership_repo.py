"""PublisherMembership persistence operations."""

from __future__ import annotations

from uuid import UUID

from cortex_api.infra.database_client import DatabaseClient
from cortex_api.service.publisher_identity.model.publisher_membership import PublisherMembership


class PublisherMembershipRepo:
    """CRUD on the `publisher_membership` table."""

    def __init__(self, database_client: DatabaseClient) -> None:
        self._db = database_client

    async def list_for_user(self, user_id: UUID) -> list[PublisherMembership]:
        raise NotImplementedError("PublisherMembershipRepo.list_for_user — implement in publisher identity slice")

    async def get(self, user_id: UUID, publisher_id: UUID) -> PublisherMembership | None:
        raise NotImplementedError("PublisherMembershipRepo.get — implement in publisher identity slice")

    async def create(self, membership: PublisherMembership) -> PublisherMembership:
        raise NotImplementedError("PublisherMembershipRepo.create — implement in publisher identity slice")

    async def delete(self, membership_id: UUID) -> None:
        raise NotImplementedError("PublisherMembershipRepo.delete — implement in publisher identity slice")
