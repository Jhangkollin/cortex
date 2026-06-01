"""GET /v1/brands — caller's brands only."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_list_my_brands_returns_only_callers_brands(
    client: TestClient,
    bootstrap_jwt,  # type: ignore[no-untyped-def]
    session_jwt,  # type: ignore[no-untyped-def]
) -> None:
    """User Dave creates two brands; user Eve creates one. /v1/brands for Dave
    returns exactly Dave's two; Eve's brand is NEVER in Dave's list.
    """
    # Dave
    bt_dave = bootstrap_jwt(oauth_subject="116000000000000000040", email="dave@m.co")
    me_dave = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {bt_dave}"})
    assert me_dave.status_code == 200
    dave_id = me_dave.json()["user_id"]
    st_dave = session_jwt(user_id=dave_id, email="dave@m.co")
    r1 = client.post("/v1/brand", headers={"Authorization": f"Bearer {st_dave}"}, json={})
    r2 = client.post("/v1/brand", headers={"Authorization": f"Bearer {st_dave}"}, json={})
    assert r1.status_code == 201 and r2.status_code == 201

    # Eve
    bt_eve = bootstrap_jwt(oauth_subject="116000000000000000041", email="eve@m.co")
    eve_id = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {bt_eve}"}).json()["user_id"]
    st_eve = session_jwt(user_id=eve_id, email="eve@m.co")
    re = client.post("/v1/brand", headers={"Authorization": f"Bearer {st_eve}"}, json={})
    assert re.status_code == 201

    # Dave lists — sees exactly two, his.
    listed = client.get("/v1/brands", headers={"Authorization": f"Bearer {st_dave}"})
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert "brands" in body
    ids = {b["id"] for b in body["brands"]}
    assert ids == {r1.json()["brand"]["id"], r2.json()["brand"]["id"]}
    # Eve's brand absent
    assert re.json()["brand"]["id"] not in ids
    # Caller's role propagated (founder → admin)
    assert all(b["role"] == "admin" for b in body["brands"])


def test_list_my_brands_unauthenticated_returns_401(client: TestClient) -> None:
    r = client.get("/v1/brands")
    assert r.status_code == 401
