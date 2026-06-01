"""Unit tests for BrandPublisherScopeRepo (smoke only — heavy lifting in integration)."""

from __future__ import annotations

from cortex_api.service.placement.repo.scope_repo import BrandPublisherScopeRepo


def test_repo_is_stateless_no_constructor_args() -> None:
    # Stateless CRUD class — caller passes AsyncSession per call
    repo = BrandPublisherScopeRepo()
    assert repo is not None
