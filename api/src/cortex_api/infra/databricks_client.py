"""Databricks SQL Warehouse client.

The official `databricks-sql-connector` is sync. To avoid blocking FastAPI's
event loop, every query is wrapped in `loop.run_in_executor(...)`. No built-in
connection pool — open-per-request via context manager. If throughput becomes
an issue, build a thin pool here.

Auth: service-principal OAuth (M2M).
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import Any

import structlog

from cortex_api.core.exceptions import UpstreamError, UpstreamTimeoutError


class DatabricksClient:
    """Thin async wrapper over `databricks-sql-connector` (sync driver)."""

    def __init__(
        self,
        host: str,
        http_path: str,
        client_id: str,
        client_secret: str,
        query_timeout_seconds: int = 30,
    ) -> None:
        self._logger = structlog.get_logger(__name__)
        self._host = host
        self._http_path = http_path
        self._client_id = client_id
        self._client_secret = client_secret
        self._timeout = query_timeout_seconds

    async def fetch_all(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
    ) -> Sequence[Sequence[Any]]:
        """Execute a SELECT and return all rows. Raises UpstreamError on failure."""
        loop = asyncio.get_running_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, self._run_query, sql, params or {}),
                timeout=self._timeout,
            )
        except TimeoutError as e:
            raise UpstreamTimeoutError(f"Databricks query timed out after {self._timeout}s") from e
        except Exception as e:
            self._logger.error("databricks_query_failed", error=str(e))
            raise UpstreamError(f"Databricks query failed: {e}") from e

    def _bare_hostname(self) -> str:
        """Strip scheme + trailing slash from the configured host.

        ``CORE_DATABRICKS_HOST`` is a full URL (``https://...cloud.databricks.com/``),
        but the connector's ``server_hostname`` wants a bare host. The SDK
        ``Config`` below still receives the full URL.
        """
        host = self._host
        for scheme in ("https://", "http://"):
            if host.startswith(scheme):
                host = host[len(scheme) :]
                break
        return host.rstrip("/")

    def _run_query(self, sql: str, params: dict[str, Any]) -> Sequence[Sequence[Any]]:
        """Sync query execution. Runs in thread pool via run_in_executor."""
        from databricks import sql as dbx_sql  # lazy import: keeps cost off the hot path

        def _credentials_provider() -> Any:
            # Service-principal M2M. Passing bare client_id/client_secret kwargs to
            # connect() does NOT select M2M — the connector falls back to U2M
            # browser OAuth (a localhost redirect) which cannot work headless. The
            # supported M2M path is an oauth_service_principal credentials_provider.
            # Imported inside the callable so it only runs when the connector
            # actually requests credentials.
            from databricks.sdk.core import Config, oauth_service_principal

            config = Config(
                host=self._host,
                client_id=self._client_id,
                client_secret=self._client_secret,
            )
            return oauth_service_principal(config)

        conn = dbx_sql.connect(
            server_hostname=self._bare_hostname(),
            http_path=self._http_path,
            credentials_provider=_credentials_provider,
        )
        try:
            cur = conn.cursor()
            try:
                cur.execute(sql, params or None)
                return list(cur.fetchall())
            finally:
                cur.close()
        finally:
            conn.close()
