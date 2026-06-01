"""Unit tests for ServiceBearerMiddleware."""

from __future__ import annotations

from typing import Any

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from cortex_api.app.middleware.service_bearer_middleware import ServiceBearerMiddleware


def _make_app(token: str) -> TestClient:
    async def ok_pub(_request: Any) -> PlainTextResponse:
        return PlainTextResponse("pub-ok")

    async def ok_brand(_request: Any) -> PlainTextResponse:
        return PlainTextResponse("brand-ok")

    routes = [
        Route("/v1/publishers/{uuid}/eligible-brands", ok_pub),
        Route("/v1/brand/{uuid}/profile", ok_brand),
    ]
    app = Starlette(routes=routes)
    app.add_middleware(ServiceBearerMiddleware, token=token)
    return TestClient(app)


class TestServiceBearerMiddleware:
    def test_valid_token_on_publishers_path_passes_through(self) -> None:
        client = _make_app("secret-token")
        r = client.get(
            "/v1/publishers/abc/eligible-brands",
            headers={"Authorization": "Bearer secret-token"},
        )
        assert r.status_code == 200
        assert r.text == "pub-ok"

    def test_missing_authorization_on_publishers_path_returns_401(self) -> None:
        client = _make_app("secret-token")
        r = client.get("/v1/publishers/abc/eligible-brands")
        assert r.status_code == 401
        assert r.headers["www-authenticate"].startswith("Bearer")
        assert r.json() == {"error": "unauthorized"}

    def test_wrong_token_returns_401(self) -> None:
        client = _make_app("secret-token")
        r = client.get(
            "/v1/publishers/abc/eligible-brands",
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert r.status_code == 401

    def test_brand_path_is_bypassed_no_auth_required(self) -> None:
        client = _make_app("secret-token")
        r = client.get("/v1/brand/abc/profile")
        assert r.status_code == 200
        assert r.text == "brand-ok"

    def test_case_sensitive_scheme_only_bearer_accepted(self) -> None:
        client = _make_app("secret-token")
        r = client.get(
            "/v1/publishers/abc/eligible-brands",
            headers={"Authorization": "bearer secret-token"},  # lowercase b
        )
        assert r.status_code == 401

    def test_empty_configured_token_rejects_all_publisher_requests(self) -> None:
        client = _make_app("")
        r = client.get(
            "/v1/publishers/abc/eligible-brands",
            headers={"Authorization": "Bearer anything"},
        )
        assert r.status_code == 401

    def test_malformed_header_no_scheme_returns_401(self) -> None:
        client = _make_app("secret-token")
        r = client.get(
            "/v1/publishers/abc/eligible-brands",
            headers={"Authorization": "secret-token"},  # no scheme
        )
        assert r.status_code == 401
