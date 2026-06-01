"""Integration test fixtures.

These tests boot the actual FastAPI app + dependency-injector containers
against a real Postgres. They catch the class of bugs that only show up
with a real DB constraint engine — partial-UNIQUE WHERE clauses, async
session lifecycles, JWT shape contracts across the web/api boundary.

Run via `pytest -m integration`. Requires Postgres reachable via either
``CORE_DB_*`` env vars OR ``CORTEX_TEST_DB_URL`` (a full
``postgresql+asyncpg://...`` DSN). See ``tests/integration/README.md``.

Fixture wiring
--------------

- ``db_url`` (session) — resolves the test DSN; fails loudly if neither
  env source is set. No SQLite fallback: integration tests exist to catch
  Postgres-specific behaviour (partial unique indexes, ENUM types).
- ``_migrations_applied`` (session, autouse) — runs ``alembic upgrade head``
  exactly once per session. Uses the same ``alembic/env.py`` prod uses, which
  reads ``CORE_DB_*``.
- ``db_engine`` (session) — async SQLAlchemy engine pointed at the test DB.
- ``_truncate_tables`` (function, autouse) — wipes rows between tests in
  reverse-FK order with ``TRUNCATE ... CASCADE``. Faster than drop/recreate.
- ``app`` (session) — the production FastAPI app object.
- ``client`` (function) — synchronous ``TestClient`` for HTTP calls.
- ``bootstrap_jwt`` / ``session_jwt`` — factory fixtures that sign HS256
  JWTs matching the contract in ``web/src/lib/cortex-token.ts``.
"""

from __future__ import annotations

import datetime as _dt
import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid5

import jwt
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

if TYPE_CHECKING:  # pragma: no cover - typing only
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

# Stable namespace UUID for bootstrap-token `sub` placeholders.
# MUST match `BOOTSTRAP_NAMESPACE` in web/src/lib/cortex-token.ts. Rotating
# this constant is a coordinated breaking change across the web/api boundary.
BOOTSTRAP_NAMESPACE = UUID("5f7d3a6e-1c4b-4b9c-9a8e-2e5f0b9b1d3c")


# --------------------------------------------------------------------------
# DB URL resolution + migrations
# --------------------------------------------------------------------------


@pytest.fixture(scope="session")
def db_url() -> str:
    """Resolve the test Postgres DSN.

    Priority: ``CORTEX_TEST_DB_URL`` (full DSN) > ``CORE_DB_*`` components.
    The CORE_DB_* fallback exists so CI (which already sets CORE_DB_*) Just
    Works without an extra env var.
    """
    explicit = os.getenv("CORTEX_TEST_DB_URL")
    if explicit:
        return explicit

    # Defer importing DatabaseConfig until we're certain pytest is collecting
    # integration tests — keeps import-time cheap for the unit suite.
    from cortex_api.core.config.database_config import DatabaseConfig

    try:
        cfg = DatabaseConfig()
    except Exception as e:  # pragma: no cover - misconfig diagnostic
        pytest.fail(
            "integration tests need Postgres but DatabaseConfig() failed: "
            f"{e!r}. Set CORTEX_TEST_DB_URL (e.g. "
            "postgresql+asyncpg://cortex:cortex@localhost:5433/cortex) or "
            "ensure CORE_DB_HOST/PORT/USERNAME/PASSWORD/NAME are exported."
        )
    return cfg.url


def _alembic_upgrade(db_url: str) -> None:
    """Run ``alembic upgrade head`` programmatically against ``db_url``.

    We don't shell out: the test process already has alembic + the
    SQLModel metadata loaded, so calling ``command.upgrade`` is both faster
    and lets the test process surface env.py exceptions directly. The
    function temporarily overrides ``sqlalchemy.url`` on the alembic
    config so the same env.py logic runs but against our test DSN.
    """
    from alembic import command
    from alembic.config import Config

    api_root = Path(__file__).resolve().parents[2]  # api/
    alembic_ini = api_root / "alembic.ini"
    if not alembic_ini.exists():  # pragma: no cover - sanity
        pytest.fail(f"alembic.ini not found at {alembic_ini}")

    cfg = Config(str(alembic_ini))
    cfg.set_main_option("script_location", str(api_root / "alembic"))
    # env.py reads DatabaseConfig() so CORE_DB_* env (or CORTEX_TEST_DB_URL
    # injected into CORE_DB_*) drives the DSN. We do NOT pass sqlalchemy.url
    # via cfg here because env.py ignores cfg.get_main_option for that key.
    command.upgrade(cfg, "head")


@pytest.fixture(scope="session", autouse=True)
def _migrations_applied(db_url: str) -> None:
    """Apply alembic migrations once per integration session.

    Autouse so any integration test that hits the DB gets a current schema
    without having to ask for the fixture explicitly. Cheap idempotent
    upgrade-to-head — no-op if already current.
    """
    # If the resolved URL is a full CORTEX_TEST_DB_URL that DIFFERS from
    # CORE_DB_*, project it back into CORE_DB_* so alembic/env.py's
    # DatabaseConfig() sees the same DSN. Common case: explicit override
    # for a non-default test DB.
    explicit = os.getenv("CORTEX_TEST_DB_URL")
    if explicit:
        _project_dsn_into_core_db_env(explicit)
    _alembic_upgrade(db_url)


def _project_dsn_into_core_db_env(dsn: str) -> None:
    """Parse ``postgresql+asyncpg://user:pwd@host:port/name`` and set
    CORE_DB_* env vars so DatabaseConfig() picks them up.

    Only used when CORTEX_TEST_DB_URL is set — gives integration tests a
    one-knob override without forcing the operator to also set CORE_DB_*.
    """
    from urllib.parse import unquote_plus, urlparse

    parsed = urlparse(dsn)
    if parsed.hostname:
        os.environ["CORE_DB_HOST"] = parsed.hostname
    if parsed.port:
        os.environ["CORE_DB_PORT"] = str(parsed.port)
    if parsed.username:
        os.environ["CORE_DB_USERNAME"] = unquote_plus(parsed.username)
    if parsed.password:
        os.environ["CORE_DB_PASSWORD"] = unquote_plus(parsed.password)
    if parsed.path and parsed.path.lstrip("/"):
        os.environ["CORE_DB_NAME"] = parsed.path.lstrip("/")


# --------------------------------------------------------------------------
# Engine + per-test truncation
# --------------------------------------------------------------------------
#
# Why function-scoped engines: pytest-asyncio creates a fresh event loop per
# test (asyncio_mode=auto, default loop scope=function). An async engine
# binds its connections to the loop it was first used on; reusing it from a
# later test's loop fails with "Task got Future attached to a different
# loop". The same constraint forces us to reset the app's DatabaseClient
# singleton between tests (see ``_reset_app_db_singletons``) — fresh DI =
# fresh engine = no cross-loop reuse.


@pytest_asyncio.fixture
async def db_engine(db_url: str) -> AsyncIterator[AsyncEngine]:
    """Function-scoped async engine for test-side assertion SQL.

    Tests use this for read-only verification (count rows, inspect FKs).
    The app itself goes through its own DatabaseClient — DO NOT use this
    engine for app-side writes; that would bypass the very DI paths we're
    trying to exercise.

    NullPool: every checkout opens a fresh asyncpg connection. With the
    default pool, the engine would cache a connection bound to the current
    test's loop, then explode when the next test reused the engine on its
    own loop. Function scope + NullPool = no cross-loop leak.
    """
    from sqlalchemy import NullPool

    engine = create_async_engine(db_url, poolclass=NullPool)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _truncate_tables(db_engine: AsyncEngine) -> None:
    """Wipe rows between tests, derived from SQLModel metadata.

    Builds the truncate list from ``SQLModel.metadata.sorted_tables`` —
    importing ``cortex_api.main`` as a side-effect registers every
    model module that has a router, so any new table joins the truncate
    set automatically as the schema grows. The hard-coded list this
    replaces (``brand_membership, brand, app_user``) silently went stale
    as new domains were scaffolded.

    Notes:
    - ``alembic_version`` is skipped — it's owned by the migration
      framework, not the test data.
    - Tables present in SQLModel metadata but not yet in the DB (e.g.
      ``publisher`` / ``publisher_membership`` exist in code at MVP but
      have no alembic migration yet) are filtered out by intersecting
      against ``information_schema.tables``. Truncating a non-existent
      table would raise; this keeps the fixture robust during the
      gap between model scaffolding and migration landing.
    - ``CASCADE`` makes FK ordering moot. ``RESTART IDENTITY`` is a
      no-op for UUID PKs but kept for the (currently theoretical) case
      of a serial column landing later.
    """
    from sqlalchemy import text
    from sqlmodel import SQLModel

    # Side-effect import: pulls every router → service → model module,
    # populating SQLModel.metadata. This is the same trick the app uses
    # at boot — no separate "import all models" registry to maintain.
    import cortex_api.main  # noqa: F401

    metadata_tables = {t.name for t in SQLModel.metadata.sorted_tables}
    metadata_tables.discard("alembic_version")
    if not metadata_tables:
        return

    async with db_engine.begin() as conn:
        result = await conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        )
        db_tables = {row[0] for row in result.all()}
        targets = sorted(metadata_tables & db_tables)
        if not targets:
            return
        quoted = ", ".join(f'"{t}"' for t in targets)
        await conn.execute(text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE"))


# --------------------------------------------------------------------------
# FastAPI app + TestClient
# --------------------------------------------------------------------------


@pytest.fixture(scope="session")
def app(_migrations_applied: None) -> FastAPI:
    """The production FastAPI app.

    We deliberately import ``cortex_api.main`` AFTER migrations have been
    applied, so the very first DatabaseClient singleton resolves against a
    schema-current DB. No DI override is necessary in the default path:
    DatabaseConfig() reads CORE_DB_*, which CI / docker-compose have already
    pointed at the test DB.

    When ``CORTEX_TEST_DB_URL`` overrides CORE_DB_*, ``_migrations_applied``
    has already projected it back into env (see
    ``_project_dsn_into_core_db_env``), so the singleton picks up the same
    DSN. No further override needed.
    """
    from cortex_api.main import app as _app

    return _app


@pytest.fixture(autouse=True)
def _reset_app_db_singletons() -> Iterator[None]:
    """Reset the app's DatabaseClient + every Singleton that holds a
    reference to it between tests.

    Each ``providers.Singleton`` is reused until reset, and its underlying
    async engine binds to the first event loop it touches. TestClient
    spins up a fresh BlockingPortal (thread + asyncio loop) per ``with``
    block, so test #2 would otherwise reuse test #1's engine on a closed
    loop and explode with "Task got Future attached to a different loop".

    Subtle gotcha: each domain Container (IdentityContainer /
    BrandIdentityContainer / PublisherIdentityContainer / ...) declares
    ``infra_container = providers.Container(InfraContainer)`` — that's a
    SEPARATE InfraContainer instance, not the one wired in main.py. So a
    fresh DatabaseClient is built per domain. Translation: we have to
    reset the database singleton inside EACH domain container's nested
    infra_container, not just the top-level one. Resetting the domain's
    own ``database_client`` (and downstream ``service`` / repo providers)
    clears their caches as well.

    Generic-by-design: we pull the container list from
    ``main._all_containers()`` and ``hasattr``-check each known
    DB-bearing provider. Resetting a provider that doesn't exist is a
    no-op; FORGETTING to reset one is a real bug (cross-event-loop
    explosion in a later test). The cost asymmetry forces the broad
    sweep.

    Follow-up architectural note (bot review on PR #19): the fact that
    every domain instantiates its own private ``InfraContainer`` — and
    therefore its own ``DatabaseClient`` / async engine — is a real cost
    here. It's why this fixture has to fan out at all. Consolidating
    onto a shared InfraContainer instance (or factoring DB resets into
    a domain-container mixin) would shrink this fixture to a single
    ``_infra_container._database_client_factory.reset()``.
    """
    # Import lazily — this conftest only loads when integration tests run,
    # but defence in depth.
    from cortex_api import main as _main

    # Providers a domain container *may* expose. hasattr-check each so the
    # set works for every container shape (e.g. brand_dashboard has no
    # `database_client` — it uses databricks_client + redis_client; that's
    # still fine because none of those bind to the asyncio loop we're
    # protecting from). Add to this list when a new shared
    # event-loop-bound provider lands.
    domain_level_provider_names = (
        "database_client",
        "service",
        # ``composer`` is BrandContainer's BrandPlacementComposer singleton; it
        # holds a DatabaseClient via its session pool, so it must reset between
        # tests for the same cross-event-loop reason ``service`` does. Added
        # for PR #52 Issue 2's concurrent-compose integration test.
        "composer",
        # eligible_brands_service holds a DatabaseClient and a cache; reset to
        # avoid cross-event-loop reuse of the DB session pool (COR-57).
        "eligible_brands_service",
        # eligible_brands_cache wraps a raw Redis connection; providers.Object
        # has no reset() so the hasattr guard skips it safely — listed here for
        # documentation so future owners know it was considered.
        "eligible_brands_cache",
        # placement_claim_service holds a DatabaseClient; reset to avoid
        # cross-event-loop reuse of the DB session pool (COR-75 / AD8).
        "placement_claim_service",
    )

    def _collect(container: object) -> list[object]:
        """Return all reset-targets on a given container instance."""
        out: list[object] = []
        # Top-level / nested InfraContainer factory. Both
        # ``_main._infra_container`` and a domain's
        # ``container.infra_container`` (a providers.Container provider that
        # proxies attribute access to the wrapped Container) expose
        # ``_database_client_factory`` directly.
        if hasattr(container, "_database_client_factory"):
            out.append(container._database_client_factory)  # type: ignore[attr-defined]
        # Domain containers wrap an InfraContainer under ``infra_container``.
        nested = getattr(container, "infra_container", None)
        if nested is not None and hasattr(nested, "_database_client_factory"):
            out.append(nested._database_client_factory)
        # Domain-level providers that may cache DatabaseClient or a Service
        # holding a DatabaseClient.
        for name in domain_level_provider_names:
            provider = getattr(container, name, None)
            if provider is not None and hasattr(provider, "reset"):
                out.append(provider)
        return out

    providers_to_reset: list[object] = []
    for container in _main._all_containers():
        providers_to_reset.extend(_collect(container))

    for p in providers_to_reset:
        p.reset()  # type: ignore[attr-defined]
    yield
    for p in providers_to_reset:
        p.reset()  # type: ignore[attr-defined]


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """Sync TestClient — one per test, no shared state.

    Async testing would require ``httpx.AsyncClient(transport=ASGITransport(...))``
    and could be added later if a test needs to drive concurrent requests;
    today the assertions are sequential, so the simpler TestClient wins.
    """
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c


# --------------------------------------------------------------------------
# JWT factories — mirror web/src/lib/cortex-token.ts
# --------------------------------------------------------------------------


def _auth_config() -> Any:
    """Return the AuthConfig instance the running app would also build.

    Reads CORE_AUTH_* env exactly the same way; tests must not hardcode the
    secret separately — the contract is "same secret, both sides".
    """
    from cortex_api.core.config.auth_config import AuthConfig

    return AuthConfig()


def _now_unix() -> int:
    return int(_dt.datetime.now(tz=_dt.UTC).timestamp())


@pytest.fixture
def bootstrap_jwt() -> Any:
    """Factory: build a bootstrap-shaped HS256 JWT.

    Signature: ``bootstrap_jwt(oauth_subject, email, display_name=None) -> str``.
    Matches the claim shape signed by ``web/src/lib/cortex-token.ts``
    ``signBootstrapToken`` so the integration tests exercise the same
    decode path that cortex-web exercises in production.
    """
    cfg = _auth_config()

    def _factory(
        oauth_subject: str,
        email: str,
        display_name: str | None = None,
        ttl_seconds: int = 60,
    ) -> str:
        now = _now_unix()
        payload: dict[str, Any] = {
            "sub": str(uuid5(BOOTSTRAP_NAMESPACE, oauth_subject)),
            "email": email,
            "oauth_subject": oauth_subject,
            "token_kind": "bootstrap",
            "iss": cfg.jwt_issuer,
            "aud": cfg.jwt_audience,
            "iat": now,
            "exp": now + ttl_seconds,
        }
        if display_name:
            payload["display_name"] = display_name
        return jwt.encode(payload, cfg.nextauth_secret, algorithm=cfg.jwt_algorithm)

    return _factory


@pytest.fixture
def session_jwt() -> Any:
    """Factory: build a session-shaped HS256 JWT.

    Signature: ``session_jwt(user_id, email, display_name=None, active_context=None) -> str``.
    Matches the claim shape signed by ``signCortexApiToken``.
    """
    cfg = _auth_config()

    def _factory(
        user_id: UUID,
        email: str,
        display_name: str | None = None,
        active_context: dict[str, Any] | None = None,
        ttl_seconds: int = 60,
    ) -> str:
        now = _now_unix()
        payload: dict[str, Any] = {
            "sub": str(user_id),
            "email": email,
            "token_kind": "session",
            "iss": cfg.jwt_issuer,
            "aud": cfg.jwt_audience,
            "iat": now,
            "exp": now + ttl_seconds,
        }
        if display_name:
            payload["display_name"] = display_name
        if active_context:
            payload["active_context"] = active_context
        return jwt.encode(payload, cfg.nextauth_secret, algorithm=cfg.jwt_algorithm)

    return _factory
