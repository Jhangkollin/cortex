# SP-1 Brand Profile Persistence — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist a brand's extracted profile in Postgres, tenant-scoped, behind real `GET`/`PUT /v1/brand/{brand_id}/profile` endpoints.

**Architecture:** A new `service/brand/` write-side domain following the existing `service/brand_identity/` pattern exactly (stateless repo taking an `AsyncSession` per call; `DatabaseClient.session()` opened in the service; `dependency_injector` container; FastAPI router with `@inject` + `active_brand` + `requires_brand_capability`). One hybrid `brand_profile` table — scalar identity columns + JSONB snapshot lists — keyed by `brand_id` (UUID v7) PK/FK → `brand.id`. One current profile per brand; `PUT` upserts.

**Tech Stack:** Python 3.12, uv, SQLModel + SQLAlchemy async (asyncpg), Alembic, FastAPI, dependency_injector, pydantic v2, pytest, ruff, mypy. Postgres via docker-compose (host `:5433`).

**Spec:** `docs/superpowers/specs/2026-05-18-sp1-brand-profile-persistence-design.md`

**Workspace:** branch `feature/sp1-brand-profile-persistence` in worktree `/Users/okis.chuang/Documents/dev/cortex-wt/sp1` (off `develop`; created during brainstorming). All commands run from that worktree root; Python commands run from its `api/` dir via `uv`. **`develop` has NO `service/brand/` or `app/api/brand/`** — this plan CREATES them (the scaffold seen earlier was uncommitted scratch on another branch; ignore it).

**Preconditions (run once before Task 1):**
```bash
cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1/api
uv sync --all-extras
docker-compose up -d            # local Postgres on host :5433 + redis
uv run alembic upgrade head     # apply 8e4ef4f9b295 + a1f4c8d2e3b5
uv run alembic heads            # confirm single head == a1f4c8d2e3b5
```

---

## File Structure

All paths under `/Users/okis.chuang/Documents/dev/cortex-wt/sp1/`.

| File | Responsibility |
|---|---|
| `api/src/cortex_api/service/brand/__init__.py` | package marker |
| `api/src/cortex_api/service/brand/model/__init__.py` | package marker |
| `api/src/cortex_api/service/brand/model/profile.py` | `BrandProfile` SQLModel (hybrid table) |
| `api/src/cortex_api/service/brand/repo/__init__.py` | package marker |
| `api/src/cortex_api/service/brand/repo/profile_repo.py` | `BrandProfileRepo` (stateless, session per call) |
| `api/src/cortex_api/service/brand/config.py` | `Config` (BaseSettings) |
| `api/src/cortex_api/service/brand/service.py` | `BrandService` (get/upsert profile) |
| `api/src/cortex_api/service/brand/container.py` | `Container` (DI) |
| `api/src/cortex_api/app/api/brand/__init__.py` | package marker |
| `api/src/cortex_api/app/api/brand/dto.py` | request/response DTOs |
| `api/src/cortex_api/app/api/brand/router.py` | `GET`/`PUT /v1/brand/{brand_id}/profile` |
| `api/src/cortex_api/main.py` | MODIFY — instantiate + wire + mount brand container/router |
| `api/alembic/env.py` | MODIFY — import `BrandProfile` for autogenerate |
| `api/alembic/versions/c3d4e5f6a7b8_brand_profile.py` | new migration |
| `api/scripts/seed_demo_brand.sql` | MODIFY — idempotent demo `brand_profile` insert |
| `api/tests/unit/test_brand_profile_model.py` | model unit tests |
| `api/tests/integration/test_brand_profile_repo.py` | repo tests (real Postgres) |
| `api/tests/unit/test_brand_service.py` | service tests (fake repo) |
| `api/tests/unit/test_brand_dto.py` | DTO tests |
| `api/tests/integration/test_brand_profile_api.py` | endpoint tests (DB + dep overrides) |
| `api/tests/unit/test_seed_sql.py` | seed-SQL content assertion |

Migration round-trip is a **manual verification procedure** (Task 8), per the
`CLAUDE.md` hard-won rule — not an automated shell-out test.

---

## Task 1: BrandProfile SQLModel

**Files:**
- Create: `api/src/cortex_api/service/brand/__init__.py`
- Create: `api/src/cortex_api/service/brand/model/__init__.py`
- Create: `api/src/cortex_api/service/brand/model/profile.py`
- Create: `api/tests/unit/test_brand_profile_model.py`

- [ ] **Step 1: Write the failing test**

Create `api/tests/unit/test_brand_profile_model.py`:

```python
from uuid import UUID

from cortex_api.core.identifiers import uuid7
from cortex_api.service.brand.model.profile import BrandProfile


def test_brand_profile_minimal_construct() -> None:
    bid = uuid7()
    p = BrandProfile(brand_id=bid, name="Acme")
    assert p.brand_id == bid
    assert p.name == "Acme"
    assert p.category_alternatives == []
    assert p.region == []
    assert p.voice_samples == []
    assert p.products == []
    assert p.competitors == []
    assert p.media_matches == []
    assert p.extraction_meta is None
    assert p.legal_name is None


def test_brand_profile_table_and_columns() -> None:
    assert BrandProfile.__tablename__ == "brand_profile"
    cols = set(BrandProfile.model_fields)
    assert {"brand_id", "name", "products", "extraction_meta", "created_at", "updated_at"} <= cols


def test_brand_profile_holds_rich_jsonb() -> None:
    p = BrandProfile(
        brand_id=uuid7(),
        name="Acme Bank",
        products=[{"name": "Card", "category": "Credit", "url": "/c", "confidence": 98}],
        competitors=[{"name": "Rival", "domain": "rival.com", "match_score": 90}],
        extraction_meta={"tier": "lite", "model": "claude-x", "cost_usd": 0.6},
    )
    assert p.products[0]["confidence"] == 98
    assert p.extraction_meta["tier"] == "lite"
    assert isinstance(p.brand_id, UUID)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1/api && uv run pytest tests/unit/test_brand_profile_model.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_api.service.brand'`

- [ ] **Step 3: Write minimal implementation**

Create `api/src/cortex_api/service/brand/__init__.py`:
```python
```
(empty file)

Create `api/src/cortex_api/service/brand/model/__init__.py`:
```python
```
(empty file)

Create `api/src/cortex_api/service/brand/model/profile.py`:
```python
"""BrandProfile SQLModel — the brand's current extracted profile.

Hybrid shape: queryable identity fields are real columns; list/nested
snapshot data is JSONB so it evolves with the extraction engine without
migrations.

Keyed by `brand_id` (UUID v7) — the universal brand scoping key, same value
as `brand.id`. Forward-compat invariant: `brand_id` equals the future
`org.id` if/when identity converges on Org/OrgMembership; nothing here
assumes a per-persona identity table. One row per brand (PK = brand_id);
PUT upserts. `extraction_meta.extracted_at` is retained so a future
versioned-history table is a clean migration, not a redesign.

OLTP write-side (Postgres) — NOT a Databricks read model.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def _jsonb_list() -> Any:
    return Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))


class BrandProfile(SQLModel, table=True):
    """A brand's current extracted profile (one row per brand)."""

    __tablename__ = "brand_profile"

    brand_id: UUID = Field(foreign_key="brand.id", primary_key=True)

    # -- scalar identity (queryable) --
    name: str = Field(max_length=255)
    legal_name: str | None = Field(default=None, max_length=255)
    tagline: str | None = Field(default=None, max_length=512)
    monogram: str | None = Field(default=None, max_length=8)
    brand_color: str | None = Field(default=None, max_length=32)
    founded: str | None = Field(default=None, max_length=32)
    about: str | None = Field(default=None)
    source_url: str | None = Field(default=None, max_length=2048)
    industry_vertical: str | None = Field(default=None, max_length=128)
    primary_jurisdiction: str | None = Field(default=None, max_length=8)
    category_value: str | None = Field(default=None, max_length=255)
    category_confidence: int | None = Field(default=None)

    # -- JSONB snapshot (evolves with the extraction engine) --
    category_alternatives: list[str] = Field(default_factory=list, sa_column=_jsonb_list())
    region: list[str] = Field(default_factory=list, sa_column=_jsonb_list())
    voice_samples: list[dict[str, Any]] = Field(default_factory=list, sa_column=_jsonb_list())
    products: list[dict[str, Any]] = Field(default_factory=list, sa_column=_jsonb_list())
    competitors: list[dict[str, Any]] = Field(default_factory=list, sa_column=_jsonb_list())
    media_matches: list[dict[str, Any]] = Field(default_factory=list, sa_column=_jsonb_list())
    extraction_meta: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )

    # -- timestamps (DB is SSOT via the migration's server_default/onupdate) --
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1/api && uv run pytest tests/unit/test_brand_profile_model.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1
git add api/src/cortex_api/service/brand/__init__.py api/src/cortex_api/service/brand/model/ api/tests/unit/test_brand_profile_model.py
git commit -m "feat(brand): BrandProfile hybrid SQLModel"
```

---

## Task 2: BrandProfileRepo

**Files:**
- Create: `api/src/cortex_api/service/brand/repo/__init__.py`
- Create: `api/src/cortex_api/service/brand/repo/profile_repo.py`
- Create: `api/tests/integration/test_brand_profile_repo.py`

> Repo tests hit real Postgres (docker-compose `:5433`), following the
> stateless-repo + session-per-call pattern from
> `service/brand_identity/repo/brand_repo.py`. A `brand` row must exist
> first (FK), created in the test via the same session.

- [ ] **Step 1: Write the failing test**

Create `api/tests/integration/test_brand_profile_repo.py`:

```python
import pytest

from cortex_api.core.identifiers import uuid7
from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.brand.model.profile import BrandProfile
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.brand_identity.model.brand import Brand

pytestmark = pytest.mark.integration


@pytest.fixture
def database_client():
    return InfraContainer()._database_client_factory()


async def test_upsert_inserts_then_get_returns(database_client) -> None:
    repo = BrandProfileRepo()
    bid = uuid7()
    async with database_client.session() as s:
        s.add(Brand(id=bid, display_name="RepoCo"))
        await s.flush()
        await repo.upsert(s, BrandProfile(brand_id=bid, name="RepoCo", region=["TW"]))

    async with database_client.session() as s:
        got = await repo.get(s, bid)
    assert got is not None
    assert got.name == "RepoCo"
    assert got.region == ["TW"]


async def test_upsert_replaces_existing(database_client) -> None:
    repo = BrandProfileRepo()
    bid = uuid7()
    async with database_client.session() as s:
        s.add(Brand(id=bid, display_name="RepoCo2"))
        await s.flush()
        await repo.upsert(s, BrandProfile(brand_id=bid, name="First", tagline="t1"))
    async with database_client.session() as s:
        await repo.upsert(
            s, BrandProfile(brand_id=bid, name="Second", products=[{"name": "P"}])
        )
    async with database_client.session() as s:
        got = await repo.get(s, bid)
    assert got is not None
    assert got.name == "Second"
    assert got.tagline is None
    assert got.products == [{"name": "P"}]


async def test_get_missing_returns_none(database_client) -> None:
    async with database_client.session() as s:
        assert await BrandProfileRepo().get(s, uuid7()) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1/api && uv run pytest tests/integration/test_brand_profile_repo.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_api.service.brand.repo.profile_repo'`

- [ ] **Step 3: Write minimal implementation**

Create `api/src/cortex_api/service/brand/repo/__init__.py`:
```python
```
(empty file)

Create `api/src/cortex_api/service/brand/repo/profile_repo.py`:
```python
"""Brand profile persistence — stateless, session per call.

Mirrors `service/brand_identity/repo/brand_repo.py`: every method takes an
`AsyncSession` so the service owns the transaction. Always brand_id-scoped.
"""

from __future__ import annotations

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from cortex_api.service.brand.model.profile import BrandProfile

# Columns PUT replaces wholesale on an existing row. brand_id (PK) and
# created_at are never overwritten; updated_at is DB-managed via onupdate.
_REPLACEABLE = (
    "name",
    "legal_name",
    "tagline",
    "monogram",
    "brand_color",
    "founded",
    "about",
    "source_url",
    "industry_vertical",
    "primary_jurisdiction",
    "category_value",
    "category_confidence",
    "category_alternatives",
    "region",
    "voice_samples",
    "products",
    "competitors",
    "media_matches",
    "extraction_meta",
)


class BrandProfileRepo:
    """CRUD on the `brand_profile` table."""

    async def get(self, session: AsyncSession, brand_id: UUID) -> BrandProfile | None:
        result = await session.exec(
            select(BrandProfile).where(BrandProfile.brand_id == brand_id)
        )
        return result.first()

    async def upsert(self, session: AsyncSession, profile: BrandProfile) -> BrandProfile:
        """Insert or wholesale-replace the single profile for `profile.brand_id`."""
        existing = await self.get(session, profile.brand_id)
        if existing is None:
            session.add(profile)
            await session.flush()
            return profile
        for col in _REPLACEABLE:
            setattr(existing, col, getattr(profile, col))
        session.add(existing)
        await session.flush()
        return existing
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1/api && uv run pytest tests/integration/test_brand_profile_repo.py -v`
Expected: PASS (3 passed)

> If a DB connection error occurs, run `docker-compose up -d` from `api/`
> and retry. If the `integration` marker is reported unknown, it is already
> registered (the repo ships a `tests/integration/` suite).

- [ ] **Step 5: Commit**

```bash
cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1
git add api/src/cortex_api/service/brand/repo/ api/tests/integration/test_brand_profile_repo.py
git commit -m "feat(brand): BrandProfileRepo get + upsert"
```

---

## Task 3: Config + Container

**Files:**
- Create: `api/src/cortex_api/service/brand/config.py`
- Create: `api/src/cortex_api/service/brand/container.py`
- Create: `api/tests/unit/test_brand_container.py`

- [ ] **Step 1: Write the failing test**

Create `api/tests/unit/test_brand_container.py`:

```python
from cortex_api.service.brand.container import Container
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.brand.service import BrandService


def test_container_provides_wired_service() -> None:
    c = Container()
    svc = c.service()
    assert isinstance(svc, BrandService)
    assert isinstance(c.profile_repo(), BrandProfileRepo)
    assert c.service() is svc  # singleton
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1/api && uv run pytest tests/unit/test_brand_container.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_api.service.brand.container'`
(`BrandService` is created in Task 4; this test stays red until Task 4. Expected — do not implement `BrandService` here.)

- [ ] **Step 3: Write minimal implementation**

Create `api/src/cortex_api/service/brand/config.py`:
```python
"""Brand (write-side) domain config."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Brand profile service config."""

    model_config = SettingsConfigDict(env_prefix="CORTEX_BRAND_", extra="forbid")
```

Create `api/src/cortex_api/service/brand/container.py`:
```python
"""Brand (write-side) domain DI container."""

from dependency_injector import containers, providers

from cortex_api.core.container import Container as CoreContainer
from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.brand.config import Config
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.brand.service import BrandService


class Container(containers.DeclarativeContainer):
    """DI container for the brand profile domain."""

    core_container = providers.Container(CoreContainer)
    infra_container = providers.Container(InfraContainer)

    config: providers.Provider[Config] = providers.Singleton(Config)

    database_client = providers.Singleton(infra_container._database_client_factory)

    profile_repo: providers.Provider[BrandProfileRepo] = providers.Singleton(BrandProfileRepo)

    service: providers.Provider[BrandService] = providers.Singleton(
        BrandService,
        database_client=database_client,
        profile_repo=profile_repo,
        config=config,
    )
```

- [ ] **Step 4: Run test to verify it fails for the right reason**

Run: `cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1/api && uv run pytest tests/unit/test_brand_container.py -v`
Expected: still FAIL — `ModuleNotFoundError: No module named 'cortex_api.service.brand.service'` (resolved in Task 4). Do not force green here.

- [ ] **Step 5: Commit**

```bash
cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1
git add api/src/cortex_api/service/brand/config.py api/src/cortex_api/service/brand/container.py api/tests/unit/test_brand_container.py
git commit -m "feat(brand): domain config + DI container (service impl next task)"
```

---

## Task 4: BrandService

**Files:**
- Create: `api/src/cortex_api/service/brand/service.py`
- Create: `api/tests/unit/test_brand_service.py`

- [ ] **Step 1: Write the failing test**

Create `api/tests/unit/test_brand_service.py`:

```python
import pytest

from cortex_api.core.exceptions import NotFoundError
from cortex_api.core.identifiers import uuid7
from cortex_api.service.brand.model.profile import BrandProfile
from cortex_api.service.brand.service import BrandService


class _FakeSessionCtx:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, *a):
        return False


class _FakeDB:
    def session(self):
        return _FakeSessionCtx()


class _FakeRepo:
    def __init__(self):
        self.store: dict = {}

    async def get(self, _session, brand_id):
        return self.store.get(brand_id)

    async def upsert(self, _session, profile):
        self.store[profile.brand_id] = profile
        return profile


def _svc(repo):
    return BrandService(database_client=_FakeDB(), profile_repo=repo, config=object())


async def test_get_profile_missing_raises_not_found() -> None:
    with pytest.raises(NotFoundError):
        await _svc(_FakeRepo()).get_profile(uuid7())


async def test_upsert_then_get_round_trips() -> None:
    repo = _FakeRepo()
    svc = _svc(repo)
    bid = uuid7()
    saved = await svc.upsert_profile(bid, BrandProfile(brand_id=bid, name="Svc Co"))
    assert saved.name == "Svc Co"
    got = await svc.get_profile(bid)
    assert got.brand_id == bid
    assert got.name == "Svc Co"


async def test_upsert_forces_tenant_brand_id() -> None:
    repo = _FakeRepo()
    svc = _svc(repo)
    tenant_bid = uuid7()
    other_bid = uuid7()
    body = BrandProfile(brand_id=other_bid, name="X")
    saved = await svc.upsert_profile(tenant_bid, body)
    assert saved.brand_id == tenant_bid  # client-supplied brand_id overridden
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1/api && uv run pytest tests/unit/test_brand_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_api.service.brand.service'`

- [ ] **Step 3: Write minimal implementation**

Create `api/src/cortex_api/service/brand/service.py`:
```python
"""BrandService — brand profile read/write use cases.

Mirrors `BrandIdentityService`: opens a `DatabaseClient.session()` per use
case, delegates persistence to a stateless repo, raises errors from
`core/exceptions.py` chained with `from e`. Scope: brand profile only —
contract / kb_source / reference_answer are out of SP-1 scope.
"""

from __future__ import annotations

from uuid import UUID

import structlog

from cortex_api.core.exceptions import NotFoundError
from cortex_api.infra.database_client import DatabaseClient
from cortex_api.service.brand.config import Config
from cortex_api.service.brand.model.profile import BrandProfile
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo


class BrandService:
    """Brand profile orchestration (write side)."""

    def __init__(
        self,
        database_client: DatabaseClient,
        profile_repo: BrandProfileRepo,
        config: Config,
    ) -> None:
        self._logger = structlog.get_logger(__name__)
        self._db = database_client
        self._profiles = profile_repo
        self._config = config

    async def get_profile(self, brand_id: UUID) -> BrandProfile:
        async with self._db.session() as session:
            profile = await self._profiles.get(session, brand_id)
            if profile is None:
                raise NotFoundError(f"brand profile for {brand_id} not found")
            return profile

    async def upsert_profile(
        self, brand_id: UUID, profile: BrandProfile
    ) -> BrandProfile:
        """Insert or wholesale-replace the brand's single current profile.

        `profile.brand_id` is forced to the tenant-scoped `brand_id` so a
        client body can never write another brand's row.
        """
        profile.brand_id = brand_id
        async with self._db.session() as session:
            saved = await self._profiles.upsert(session, profile)
        self._logger.info("brand_profile_upserted", brand_id=str(brand_id))
        return saved
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1/api && uv run pytest tests/unit/test_brand_service.py tests/unit/test_brand_container.py -v`
Expected: PASS (test_brand_service: 3 passed; test_brand_container: 1 passed — now green)

- [ ] **Step 5: Commit**

```bash
cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1
git add api/src/cortex_api/service/brand/service.py api/tests/unit/test_brand_service.py
git commit -m "feat(brand): BrandService get_profile + upsert_profile"
```

---

## Task 5: DTOs

**Files:**
- Create: `api/src/cortex_api/app/api/brand/__init__.py`
- Create: `api/src/cortex_api/app/api/brand/dto.py`
- Create: `api/tests/unit/test_brand_dto.py`

- [ ] **Step 1: Write the failing test**

Create `api/tests/unit/test_brand_dto.py`:

```python
from cortex_api.app.api.brand.dto import BrandProfileResponse, UpsertProfileRequest
from cortex_api.core.identifiers import uuid7
from cortex_api.service.brand.model.profile import BrandProfile


def test_upsert_request_minimal_requires_only_name() -> None:
    req = UpsertProfileRequest(name="Acme")
    assert req.name == "Acme"
    assert req.products == []
    assert req.legal_name is None


def test_upsert_request_typed_nested_and_to_model() -> None:
    bid = uuid7()
    req = UpsertProfileRequest(
        name="Acme",
        products=[{"name": "Card", "category": "Credit", "url": "/c", "confidence": 98}],
        category={"value": "Banking", "confidence": 95, "alternatives": ["FinTech"]},
    )
    assert req.products[0].confidence == 98
    assert req.category.alternatives == ["FinTech"]
    m = req.to_model(bid)
    assert m.brand_id == bid
    assert m.category_value == "Banking"
    assert m.category_confidence == 95
    assert m.category_alternatives == ["FinTech"]
    assert m.products == [{"name": "Card", "category": "Credit", "url": "/c", "confidence": 98}]


def test_response_from_model() -> None:
    bid = uuid7()
    model = BrandProfile(brand_id=bid, name="Acme", region=["TW"])
    resp = BrandProfileResponse.from_model(model)
    assert resp.brand_id == bid
    assert resp.name == "Acme"
    assert resp.region == ["TW"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1/api && uv run pytest tests/unit/test_brand_dto.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_api.app.api.brand'`

- [ ] **Step 3: Write minimal implementation**

Create `api/src/cortex_api/app/api/brand/__init__.py`:
```python
```
(empty file)

Create `api/src/cortex_api/app/api/brand/dto.py`:
```python
"""Brand profile DTOs.

The request is the persistable subset a caller PUTs. SP-1 does NOT import
cortex-brand-extract; mapping the SP-2 `BrandProfile` extraction type to
`UpsertProfileRequest` is SP-3's `HttpOnboardingApi` projection job.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from cortex_api.service.brand.model.profile import BrandProfile


class ProductDTO(BaseModel):
    name: str
    category: str | None = None
    url: str | None = None
    confidence: int = 0


class CompetitorDTO(BaseModel):
    name: str
    domain: str | None = None
    match_score: int = 0


class VoiceSampleDTO(BaseModel):
    src: str
    text: str


class MediaMatchDTO(BaseModel):
    outlet_id: str
    name: str
    relevance: int = 0


class CategoryDTO(BaseModel):
    value: str | None = None
    confidence: int | None = None
    alternatives: list[str] = Field(default_factory=list)


class UpsertProfileRequest(BaseModel):
    """Body for `PUT /v1/brand/{brand_id}/profile`. Only `name` is required."""

    name: str = Field(min_length=1, max_length=255)
    legal_name: str | None = None
    tagline: str | None = None
    monogram: str | None = None
    brand_color: str | None = None
    founded: str | None = None
    about: str | None = None
    source_url: str | None = None
    industry_vertical: str | None = None
    primary_jurisdiction: str | None = None
    category: CategoryDTO | None = None
    region: list[str] = Field(default_factory=list)
    voice_samples: list[VoiceSampleDTO] = Field(default_factory=list)
    products: list[ProductDTO] = Field(default_factory=list)
    competitors: list[CompetitorDTO] = Field(default_factory=list)
    media_matches: list[MediaMatchDTO] = Field(default_factory=list)
    extraction_meta: dict[str, Any] | None = None

    def to_model(self, brand_id: UUID) -> BrandProfile:
        cat = self.category
        return BrandProfile(
            brand_id=brand_id,
            name=self.name,
            legal_name=self.legal_name,
            tagline=self.tagline,
            monogram=self.monogram,
            brand_color=self.brand_color,
            founded=self.founded,
            about=self.about,
            source_url=self.source_url,
            industry_vertical=self.industry_vertical,
            primary_jurisdiction=self.primary_jurisdiction,
            category_value=cat.value if cat else None,
            category_confidence=cat.confidence if cat else None,
            category_alternatives=cat.alternatives if cat else [],
            region=list(self.region),
            voice_samples=[v.model_dump() for v in self.voice_samples],
            products=[p.model_dump() for p in self.products],
            competitors=[c.model_dump() for c in self.competitors],
            media_matches=[m.model_dump() for m in self.media_matches],
            extraction_meta=self.extraction_meta,
        )


class BrandProfileResponse(BaseModel):
    brand_id: UUID
    name: str
    legal_name: str | None = None
    tagline: str | None = None
    monogram: str | None = None
    brand_color: str | None = None
    founded: str | None = None
    about: str | None = None
    source_url: str | None = None
    industry_vertical: str | None = None
    primary_jurisdiction: str | None = None
    category_value: str | None = None
    category_confidence: int | None = None
    category_alternatives: list[str] = Field(default_factory=list)
    region: list[str] = Field(default_factory=list)
    voice_samples: list[dict[str, Any]] = Field(default_factory=list)
    products: list[dict[str, Any]] = Field(default_factory=list)
    competitors: list[dict[str, Any]] = Field(default_factory=list)
    media_matches: list[dict[str, Any]] = Field(default_factory=list)
    extraction_meta: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, m: BrandProfile) -> "BrandProfileResponse":
        return cls(
            brand_id=m.brand_id,
            name=m.name,
            legal_name=m.legal_name,
            tagline=m.tagline,
            monogram=m.monogram,
            brand_color=m.brand_color,
            founded=m.founded,
            about=m.about,
            source_url=m.source_url,
            industry_vertical=m.industry_vertical,
            primary_jurisdiction=m.primary_jurisdiction,
            category_value=m.category_value,
            category_confidence=m.category_confidence,
            category_alternatives=m.category_alternatives,
            region=m.region,
            voice_samples=m.voice_samples,
            products=m.products,
            competitors=m.competitors,
            media_matches=m.media_matches,
            extraction_meta=m.extraction_meta,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1/api && uv run pytest tests/unit/test_brand_dto.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1
git add api/src/cortex_api/app/api/brand/__init__.py api/src/cortex_api/app/api/brand/dto.py api/tests/unit/test_brand_dto.py
git commit -m "feat(brand): profile request/response DTOs"
```

---

## Task 6: Router

**Files:**
- Create: `api/src/cortex_api/app/api/brand/router.py`
- Create: `api/tests/integration/test_brand_profile_api.py`

> Endpoint tests override `authenticated_user` (so `active_brand` builds a
> `BrandTenantCtx` with the needed capabilities) and hit the real DB —
> mirroring the existing integration suite style.

- [ ] **Step 1: Write the failing test**

Create `api/tests/integration/test_brand_profile_api.py`:

```python
import pytest
from fastapi.testclient import TestClient

from cortex_api.app.dependencies.auth import authenticated_user
from cortex_api.core.identifiers import uuid7
from cortex_api.infra.container import Container as InfraContainer
from cortex_api.main import create_app
from cortex_api.service.brand_identity.model.brand import Brand
from cortex_api.service.identity.model.authed_user import AuthedUser

pytestmark = pytest.mark.integration


def _authed(brand_id, caps):
    return AuthedUser(
        user_id=uuid7(),
        email="t@example.com",
        display_name="T",
        raw_claims={
            "active_context": {
                "kind": "brand",
                "id": str(brand_id),
                "role": "admin",
                "capabilities": caps,
            }
        },
    )


@pytest.fixture
async def brand_id():
    bid = uuid7()
    db = InfraContainer()._database_client_factory()
    async with db.session() as s:
        s.add(Brand(id=bid, display_name="ApiCo"))
        await s.flush()
    return bid


def _client(brand_id, caps):
    app = create_app()
    app.dependency_overrides[authenticated_user] = lambda: _authed(brand_id, caps)
    return TestClient(app)


async def test_get_missing_profile_404(brand_id) -> None:
    c = _client(brand_id, ["view_brand_dashboard"])
    assert c.get(f"/v1/brand/{brand_id}/profile").status_code == 404


async def test_put_then_get_round_trip(brand_id) -> None:
    c = _client(brand_id, ["view_brand_dashboard", "edit_brand_settings"])
    put = c.put(
        f"/v1/brand/{brand_id}/profile",
        json={"name": "ApiCo", "region": ["TW"],
              "products": [{"name": "Card", "category": "Credit"}]},
    )
    assert put.status_code == 200, put.text
    assert put.json()["name"] == "ApiCo"
    got = c.get(f"/v1/brand/{brand_id}/profile")
    assert got.status_code == 200
    body = got.json()
    assert body["region"] == ["TW"]
    assert body["products"][0]["name"] == "Card"


async def test_put_without_capability_403(brand_id) -> None:
    c = _client(brand_id, ["view_brand_dashboard"])  # no edit_brand_settings
    assert c.put(f"/v1/brand/{brand_id}/profile", json={"name": "X"}).status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1/api && uv run pytest tests/integration/test_brand_profile_api.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_api.app.api.brand.router'` (and, after Step 3 but before Task 7, route 404 because the router is not yet mounted).

- [ ] **Step 3: Write minimal implementation**

Create `api/src/cortex_api/app/api/brand/router.py`:
```python
"""Brand profile endpoints — tenant-scoped read/write.

Pattern mirrors `app/api/brand_identity/router.py`: explicit `/v1/brand`
paths, `@inject` + `Provide[BrandContainer.service]`, `active_brand` builds
the BrandTenantCtx from JWT claims, capability gates via
`requires_brand_capability`. Service raises `NotFoundError`; the app's
registered exception handlers map it to HTTP 404.
"""

from __future__ import annotations

from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from cortex_api.app.api.brand.dto import BrandProfileResponse, UpsertProfileRequest
from cortex_api.app.dependencies.brand import active_brand
from cortex_api.app.dependencies.capability import requires_brand_capability
from cortex_api.service.brand.container import Container as BrandContainer
from cortex_api.service.brand.service import BrandService
from cortex_api.service.brand_identity.model.brand_capability import BrandCapability
from cortex_api.service.brand_identity.model.brand_tenant_ctx import BrandTenantCtx

router = APIRouter(tags=["brand"])


@router.get(
    "/v1/brand/{brand_id}/profile",
    response_model=BrandProfileResponse,
    summary="Get the brand's current profile",
    dependencies=[Depends(requires_brand_capability(BrandCapability.VIEW_BRAND_DASHBOARD))],
)
@inject
async def get_brand_profile(
    brand_id: UUID,
    tenant: BrandTenantCtx = Depends(active_brand),
    brand_service: BrandService = Depends(Provide[BrandContainer.service]),
) -> BrandProfileResponse:
    profile = await brand_service.get_profile(tenant.brand_id)
    return BrandProfileResponse.from_model(profile)


@router.put(
    "/v1/brand/{brand_id}/profile",
    response_model=BrandProfileResponse,
    summary="Upsert (insert-or-replace) the brand's current profile",
    dependencies=[Depends(requires_brand_capability(BrandCapability.EDIT_BRAND_SETTINGS))],
)
@inject
async def upsert_brand_profile(
    brand_id: UUID,
    body: UpsertProfileRequest,
    tenant: BrandTenantCtx = Depends(active_brand),
    brand_service: BrandService = Depends(Provide[BrandContainer.service]),
) -> BrandProfileResponse:
    saved = await brand_service.upsert_profile(
        tenant.brand_id, body.to_model(tenant.brand_id)
    )
    return BrandProfileResponse.from_model(saved)
```

- [ ] **Step 4: Run test to verify it still fails (router not mounted yet)**

Run: `cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1/api && uv run pytest tests/integration/test_brand_profile_api.py -v`
Expected: FAIL — routes 404 / `BrandContainer` not wired. Reachable in Task 7. Do not force green here.

- [ ] **Step 5: Commit**

```bash
cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1
git add api/src/cortex_api/app/api/brand/router.py api/tests/integration/test_brand_profile_api.py
git commit -m "feat(brand): GET/PUT /v1/brand/{brand_id}/profile router"
```

---

## Task 7: Wire into main.py

**Files:**
- Modify: `api/src/cortex_api/main.py`

- [ ] **Step 1: The failing test is Task 6's API test**

Run: `cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1/api && uv run pytest tests/integration/test_brand_profile_api.py -v`
Expected: FAIL (router not mounted).

- [ ] **Step 2: Modify `main.py`**

Add the router import after the `brand_identity` router import (~line 17):
```python
from cortex_api.app.api.brand.router import router as brand_router
```

Add the container import after the `BrandIdentityContainer` import (~line 29):
```python
from cortex_api.service.brand.container import Container as BrandContainer
```

Instantiate it after `_brand_identity_container` (~line 38):
```python
_brand_container = BrandContainer()
```

Add it to the `_all_containers()` returned tuple, before the `# Add new domain containers here.` comment:
```python
        _brand_container,
```

Add a `wire()` call after the `_brand_identity_container.wire(...)` block (~line 113):
```python
    _brand_container.wire(modules=["cortex_api.app.api.brand.router"])
```

Mount the router after `app.include_router(brand_identity_router)` (~line 118):
```python
    app.include_router(brand_router)
```

- [ ] **Step 3: Run the API + smoke tests to verify they pass**

Run: `cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1/api && uv run pytest tests/integration/test_brand_profile_api.py tests/unit/test_app_boots.py -v`
Expected: PASS (3 API tests pass; app-boots smoke test still passes with new routes)

- [ ] **Step 4: Run the full suite (no regressions)**

Run: `cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1/api && uv run pytest -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1
git add api/src/cortex_api/main.py
git commit -m "feat(brand): wire BrandContainer + mount profile router"
```

---

## Task 8: Alembic migration (+ manual round-trip verification)

**Files:**
- Modify: `api/alembic/env.py`
- Create: `api/alembic/versions/c3d4e5f6a7b8_brand_profile.py`

- [ ] **Step 1: Modify `api/alembic/env.py`**

Add after the `brand_membership` import (~line 27), keeping `# noqa: F401`:
```python
from cortex_api.service.brand.model.profile import BrandProfile  # noqa: F401
```

- [ ] **Step 2: Create the migration**

Create `api/alembic/versions/c3d4e5f6a7b8_brand_profile.py`:
```python
"""brand_profile (hybrid: scalar columns + JSONB snapshot)

Revision ID: c3d4e5f6a7b8
Revises: a1f4c8d2e3b5
Create Date: 2026-05-18 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "a1f4c8d2e3b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "brand_profile",
        sa.Column("brand_id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("legal_name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("tagline", sqlmodel.sql.sqltypes.AutoString(length=512), nullable=True),
        sa.Column("monogram", sqlmodel.sql.sqltypes.AutoString(length=8), nullable=True),
        sa.Column("brand_color", sqlmodel.sql.sqltypes.AutoString(length=32), nullable=True),
        sa.Column("founded", sqlmodel.sql.sqltypes.AutoString(length=32), nullable=True),
        sa.Column("about", sa.Text(), nullable=True),
        sa.Column("source_url", sqlmodel.sql.sqltypes.AutoString(length=2048), nullable=True),
        sa.Column("industry_vertical", sqlmodel.sql.sqltypes.AutoString(length=128), nullable=True),
        sa.Column("primary_jurisdiction", sqlmodel.sql.sqltypes.AutoString(length=8), nullable=True),
        sa.Column("category_value", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("category_confidence", sa.Integer(), nullable=True),
        sa.Column("category_alternatives", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'[]'::jsonb")),
        sa.Column("region", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'[]'::jsonb")),
        sa.Column("voice_samples", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'[]'::jsonb")),
        sa.Column("products", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'[]'::jsonb")),
        sa.Column("competitors", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'[]'::jsonb")),
        sa.Column("media_matches", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'[]'::jsonb")),
        sa.Column("extraction_meta", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(["brand_id"], ["brand.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("brand_id"),
    )


def downgrade() -> None:
    op.drop_table("brand_profile")
    # No ENUM created by this migration → no sa.Enum(...).drop() needed.
```

- [ ] **Step 3: Manual round-trip verification (the hard-won CLAUDE.md rule)**

Run each, confirming each exits 0:
```bash
cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1/api
uv run alembic upgrade head      # expect: applies c3d4e5f6a7b8, no error
uv run alembic downgrade base    # expect: drops everything incl. brand_profile, no error
uv run alembic upgrade head      # expect: re-applies cleanly (catches missed enum drops — none here)
uv run alembic heads             # expect: single head 'c3d4e5f6a7b8'
```
Expected: all four succeed; final `heads` prints `c3d4e5f6a7b8 (head)`.

- [ ] **Step 4: Confirm prior DB-touching tests still pass on the migrated schema**

Run: `cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1/api && uv run pytest tests/integration/test_brand_profile_repo.py tests/integration/test_brand_profile_api.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1
git add api/alembic/env.py api/alembic/versions/c3d4e5f6a7b8_brand_profile.py
git commit -m "feat(brand): brand_profile migration (hybrid, no enum → clean downgrade)"
```

---

## Task 9: Seed extension

**Files:**
- Modify: `api/scripts/seed_demo_brand.sql`
- Create: `api/tests/unit/test_seed_sql.py`

- [ ] **Step 1: Write the failing test**

Create `api/tests/unit/test_seed_sql.py`:

```python
from pathlib import Path

_SEED = (
    Path(__file__).resolve().parents[2] / "scripts" / "seed_demo_brand.sql"
).read_text()


def test_seed_inserts_brand_profile_idempotently() -> None:
    assert "INSERT INTO brand_profile" in _SEED
    assert "ON CONFLICT (brand_id) DO NOTHING" in _SEED


def test_seed_brand_profile_runs_before_commit() -> None:
    assert _SEED.rstrip().endswith("COMMIT;")
    assert _SEED.index("INSERT INTO brand_profile") < _SEED.rindex("COMMIT;")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1/api && uv run pytest tests/unit/test_seed_sql.py -v`
Expected: FAIL — `assert "INSERT INTO brand_profile" in _SEED` is False.

- [ ] **Step 3: Modify `api/scripts/seed_demo_brand.sql`**

Insert immediately before the final `COMMIT;` line:
```sql
INSERT INTO brand_profile (brand_id, name, industry_vertical)
VALUES (
    :brand_id::uuid,
    :'display_name',
    NULLIF(:'industry', '')
)
ON CONFLICT (brand_id) DO NOTHING;
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1/api && uv run pytest tests/unit/test_seed_sql.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1
git add api/scripts/seed_demo_brand.sql api/tests/unit/test_seed_sql.py
git commit -m "feat(brand): seed an idempotent demo brand_profile"
```

---

## Task 10: Full quality gate

**Files:** none (verification + fixups only)

- [ ] **Step 1: Run the full gate**

Run:
```bash
cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1/api
uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest -q
```
Expected: ruff clean, format clean, mypy clean, all tests pass (integration needs docker-compose Postgres up + `alembic upgrade head` applied).

- [ ] **Step 2: Fix any findings**

Apply only minimal, correct fixes for ruff/mypy/format issues introduced by SP-1 files (import order, unused import, missing return annotation). Do NOT modify unrelated modules. If `ruff format --check` fails, run `uv run ruff format .` then re-verify. Re-run until fully green.

- [ ] **Step 3: Commit (only if fixups were needed)**

```bash
cd /Users/okis.chuang/Documents/dev/cortex-wt/sp1
git add -A api/
git commit -m "chore(brand): satisfy ruff/mypy/format gate"
```

---

## Self-Review

**1. Spec coverage**

| Spec requirement | Task |
|---|---|
| Decision 1 — full vertical slice, brand_profile only | 1–9; contract/kb/ref-answer NOT created (out of scope honored) |
| Decision 2 — `brand.id` UUID PK/FK + forward-compat note | Task 1 (model + docstring invariant); Task 8 (FK CASCADE) |
| Decision 3 — hybrid scalar columns + JSONB | Task 1 + Task 8 |
| Decision 4 — single current profile, PUT upsert | Tasks 2, 4, 6 |
| Repo `get`/`upsert`, brand_id-scoped | Task 2 |
| Service `get_profile` (NotFoundError) / `upsert_profile` (forces tenant brand_id) | Task 4 |
| `GET`/`PUT /v1/brand/{brand_id}/profile` + capabilities | Task 6 (VIEW_BRAND_DASHBOARD / EDIT_BRAND_SETTINGS) |
| DI wiring (BrandContainer + router mount + _all_containers) | Task 7 |
| Migration: env.py import, no enum, manual round-trip | Task 8 |
| Seed: idempotent demo brand_profile | Task 9 |
| Testing: model/repo/service/dto/api + round-trip + seed | Tasks 1–9 |
| No cortex-brand-extract import; SP-3 owns projection | Task 5 dto docstring; not imported anywhere |
| Out of scope: contract/kb/ref-answer, Org, publisher, history | honored — no such tasks |
| `updated_at` onupdate via migration (DB SSOT) | Task 8 column def |

No gaps.

**2. Placeholder scan:** No "TBD/TODO/handle edge cases". Every code step has complete content. The two intentionally-red checkpoints (Task 3 Step 4, Task 6 Step 4) state precisely why and which later task turns them green — sequencing, not placeholders. Migration round-trip is an explicit manual `Run:` procedure with expected output (per CLAUDE.md), not an automated shell-out.

**3. Type consistency:** `BrandProfile` field names are identical across model (T1), repo `_REPLACEABLE` (T2), service (T4), DTO `to_model`/`from_model` (T5), migration columns (T8). `BrandService.__init__(database_client, profile_repo, config)` matches the container provider (T3) and the fake in the service test (T4). `BrandProfileRepo.get(session, brand_id)` / `upsert(session, profile)` match every caller. Capability members (`VIEW_BRAND_DASHBOARD`, `EDIT_BRAND_SETTINGS`) match `brand_capability.py`. Path `/v1/brand/{brand_id}/profile` consistent across router and API tests. Migration `down_revision = "a1f4c8d2e3b5"` matches the current head.

Plan is internally consistent and fully covers the approved spec.
