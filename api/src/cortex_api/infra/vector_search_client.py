"""Databricks Vector Search client.

Always filters by an active-context namespace to enforce multi-tenancy. Used by
the knowledge_base service (placeholder at MVP scaffolding).
"""

from __future__ import annotations

from typing import Any

import structlog


class VectorSearchClient:
    """Thin async wrapper around Databricks Vector Search SDK (placeholder)."""

    def __init__(self, endpoint: str, index: str) -> None:
        self._logger = structlog.get_logger(__name__)
        self._endpoint = endpoint
        self._index = index

    async def query(
        self,
        text: str,
        vector_namespace: str,
        k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Vector similarity search. Always filters by `vector_namespace`."""
        # NOTE: stub — real implementation hits databricks-vectorsearch SDK.
        raise NotImplementedError("VectorSearchClient.query — wire when knowledge_base lands")

    async def close(self) -> None:
        return None
