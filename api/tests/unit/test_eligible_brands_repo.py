"""Smoke test for EligibleBrandsRepo (real query coverage lives in integration)."""

from __future__ import annotations

from cortex_api.service.placement.repo.eligible_brands_repo import EligibleBrandsRepo


def test_repo_is_stateless_no_constructor_args() -> None:
    repo = EligibleBrandsRepo()
    assert repo is not None
