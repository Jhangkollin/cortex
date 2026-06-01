"""Publisher persistence operations."""

from __future__ import annotations

from uuid import UUID

from cortex_api.infra.database_client import DatabaseClient
from cortex_api.service.publisher_identity.model.publisher import Publisher


class PublisherRepo:
    """CRUD on the `publisher` table."""

    def __init__(self, database_client: DatabaseClient) -> None:
        self._db = database_client

    async def get_by_id(self, publisher_id: UUID) -> Publisher | None:
        raise NotImplementedError("PublisherRepo.get_by_id — implement in publisher identity slice")

    async def create(self, publisher: Publisher) -> Publisher:
        raise NotImplementedError("PublisherRepo.create — implement in publisher identity slice")

    async def archive(self, publisher_id: UUID) -> None:
        raise NotImplementedError("PublisherRepo.archive — implement in publisher identity slice")
