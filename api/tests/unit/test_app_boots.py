"""Smoke test — verifies the whole DI graph wires up without errors.

If this passes, the app boots. It doesn't test behaviour — just that every
container, every import, every router registration completes cleanly.
"""

from __future__ import annotations


def test_main_imports() -> None:
    """Import cortex_api.main and confirm the FastAPI app instance exists."""
    from cortex_api import main

    assert main.app is not None
    assert main.app.title == "Cortex API"


def test_routes_registered() -> None:
    """All expected routers are mounted."""
    from cortex_api.main import app

    paths = {getattr(route, "path", "") for route in app.routes}
    # Public infra routes
    assert "/health" in paths
    assert "/version" in paths
    # Auth routes — Pattern B (no /switch-context; cortex-api enriches NextAuth-signed JWTs).
    assert "/v1/auth/me" in paths
    assert "/v1/auth/resolve-context" in paths
    # Brand identity — collection (create) + resource (get/patch + members).
    assert "/v1/brand" in paths
    assert "/v1/brand/{brand_id}" in paths
    assert "/v1/brand/{brand_id}/users" in paths
    assert "/v1/brand/{brand_id}/analytics/metrics" in paths
    assert "/v1/brand/{brand_id}/analytics/metrics/by-publisher" in paths
    # Publisher identity + dashboard metrics
    assert "/v1/publisher/{publisher_id}" in paths
    assert "/v1/publisher/{publisher_id}/analytics/metrics" in paths
    # F2 eligible-brands (service-to-service)
    assert "/v1/publishers/{publisher_uuid}/eligible-brands" in paths


def test_health_endpoint() -> None:
    """Hit /health with a TestClient and confirm 200 OK."""
    from fastapi.testclient import TestClient

    from cortex_api.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
