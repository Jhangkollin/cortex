"""Path-scoped Bearer middleware for service-to-service auth.

Applies to requests whose path begins with ``/v1/publishers/``. Other paths
pass through untouched (user-facing routes use NextAuth + FastAPI Depends).

Per cortex CLAUDE.md: middleware is pure ASGI, no BaseHTTPMiddleware.
"""

from __future__ import annotations

import json
import secrets

import structlog
from starlette.types import ASGIApp, Receive, Scope, Send

_LOG = structlog.get_logger(__name__)

_PATH_PREFIX = "/v1/publishers/"
_UNAUTHORIZED_BODY = json.dumps({"error": "unauthorized"}).encode("utf-8")


class ServiceBearerMiddleware:
    """Validate Bearer token on /v1/publishers/* paths only."""

    def __init__(self, app: ASGIApp, token: str) -> None:
        self.app = app
        self._token = token
        if not token:
            _LOG.warning("service_token_not_configured", scope="agent_ws")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope["path"].startswith(_PATH_PREFIX):
            await self.app(scope, receive, send)
            return

        if not self._token or not self._token_matches(scope):
            await self._send_unauthorized(send)
            return

        await self.app(scope, receive, send)

    def _token_matches(self, scope: Scope) -> bool:
        header = self._read_authorization_header(scope)
        if header is None:
            return False
        # Case-sensitive scheme per RFC 6750
        if not header.startswith("Bearer "):
            return False
        provided = header[len("Bearer ") :]
        return secrets.compare_digest(provided, self._token)

    @staticmethod
    def _read_authorization_header(scope: Scope) -> str | None:
        for name_bytes, value_bytes in scope.get("headers", []):
            name: bytes = name_bytes
            value: bytes = value_bytes
            if name.lower() == b"authorization":
                return value.decode("latin-1")
        return None

    @staticmethod
    async def _send_unauthorized(send: Send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"www-authenticate", b'Bearer realm="cortex-service"'),
                    (b"content-length", str(len(_UNAUTHORIZED_BODY)).encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": _UNAUTHORIZED_BODY})
