"""Pytest fixtures — DI container overrides for testing.

Mirrors agent-will-smith's conftest pattern: override container providers
instead of `mock.patch`. Each test gets a fresh container.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock

import pytest

from cortex_api.core.container import Container as CoreContainer
from cortex_api.infra.container import Container as InfraContainer


@pytest.fixture
def core_container() -> Iterator[CoreContainer]:
    container = CoreContainer()
    yield container
    container.unwire()


@pytest.fixture
def infra_container(core_container: CoreContainer) -> Iterator[InfraContainer]:
    container = InfraContainer()
    container.core_container.override(core_container)
    yield container
    container.unwire()


@pytest.fixture
def mock_databricks_client() -> MagicMock:
    client = MagicMock()
    client.fetch_all = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_redis_client() -> MagicMock:
    client = MagicMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock(return_value=None)
    client.delete = AsyncMock(return_value=None)
    return client
