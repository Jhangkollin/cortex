# SP-3a — Product-mode HttpOnboardingApi + Analyze Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the onboarding wizard's `analyzeBrand` real in authenticated product mode — a real URL runs server-side SP-2 extraction (async job + poll), persists via SP-1, projects to `ExtractedBrand` for the unchanged wizard.

**Architecture:** New `brand_profile_analysis_job` table + a dedicated `AnalyzeJobService` whose in-process `asyncio` worker `await`s SP-2's async `extract_brand_profile`, maps the result onto SP-1's `BrandProfile`, and upserts it. Two tenant-scoped routes on the existing brand router (`POST …/profile/analyze` → 202+job_id, `GET …/profile/analyze/{job_id}` → status[+profile]). The web `HttpOnboardingApi` calls a Server Action (server-only token signing), polls, and owns the `BrandProfile → ExtractedBrand` projection.

**Tech Stack:** FastAPI, SQLModel + asyncpg + Alembic, dependency-injector, structlog, Pydantic v2, `cortex-brand-extract` (SP-2 lib), Next.js 16 App Router + Server Actions, vitest.

**Worktree:** `/Users/okis.chuang/Documents/dev/cortex-wt/sp3a` (branch `feature/sp3a-analyze-pipeline`, off develop@`3077f90`). Spec: `docs/superpowers/specs/2026-05-18-sp3a-analyze-pipeline-design.md`.

**Conventions (do not deviate):** stateless repos take `session: AsyncSession`; the service owns the transaction via `async with self._db.session()`. `structlog.get_logger(__name__)` in `__init__`. Exceptions only from `cortex_api.core.exceptions`, chained `from e` when re-raising. Tests override DI providers, never `mock.patch`. Empty `__init__.py`. CI runs (from `api/`) `uv run ruff check src tests` + `uv run ruff format --check src tests` + `uv run mypy src`; **run `uv run ruff clean` before lint** (stale-cache masking is a known trap). Postgres for tests: docker-compose host `:5433` (`cd api && docker-compose up -d`); scope env to `CORE_DB_*`/`CORE_AUTH_NEXTAUTH_SECRET` if a local `.env` CORS value will not JSON-parse. Commit message bodies end with exactly `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`.

**Doc note for the executor:** TypeScript snippets below use string concatenation for URLs/messages (a docs-write security heuristic rejects backtick-interpolation in saved files). When implementing, write idiomatic template literals — the house eslint enforces `prefer-template`. Behaviour is identical; convert concatenation → template literal as you type.

---

## Task 1: Wire `cortex-brand-extract` into cortex-api

**Files:**
- Modify: `api/pyproject.toml` (`[project] dependencies`, add `[tool.uv.sources]`)
- Test: `api/tests/unit/test_sp2_import.py`

- [ ] **Step 1: Write the failing test**

```python
# api/tests/unit/test_sp2_import.py
"""SP-2 (cortex-brand-extract) must be importable from cortex-api."""


def test_cortex_brand_extract_importable() -> None:
    from cortex_brand_extract import BrandProfile, ProviderConfig, extract_brand_profile

    assert callable(extract_brand_profile)
    assert BrandProfile.__name__ == "BrandProfile"
    assert ProviderConfig.__name__ == "ProviderConfig"


def test_claude_provider_importable() -> None:
    from cortex_brand_extract.llm.claude import ClaudeProvider

    assert ClaudeProvider.__name__ == "ClaudeProvider"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd api && uv run pytest tests/unit/test_sp2_import.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_brand_extract'`

- [ ] **Step 3: Add the dependency + uv source**

In `api/pyproject.toml`, add to the `[project] dependencies` array (after `"httpx>=0.27.0",`):

```toml
    "cortex-brand-extract>=0.1.0",
```

Add a new top-level table (after `[project.optional-dependencies]`, before `[tool.ruff]`):

```toml
[tool.uv.sources]
cortex-brand-extract = { path = "../packages/brand-extract", editable = true }
```

- [ ] **Step 4: Sync and verify**

Run: `cd api && uv sync --all-extras && uv run pytest tests/unit/test_sp2_import.py -v`
Expected: PASS (2 passed). If `uv sync` errors on the path, confirm `../packages/brand-extract/pyproject.toml` exists relative to `api/`.

- [ ] **Step 5: Commit**

```bash
cd /Users/okis.chuang/Documents/dev/cortex-wt/sp3a
git add api/pyproject.toml api/uv.lock api/tests/unit/test_sp2_import.py
git commit -m "build(api): wire cortex-brand-extract (SP-2) as an editable path dep

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: `AnalyzeJobStatus` enum + `BrandProfileAnalysisJob` SQLModel

**Files:**
- Create: `api/src/cortex_api/service/brand/model/analysis_job.py`
- Modify: `api/alembic/env.py` (autogenerate import)
- Test: `api/tests/unit/test_analysis_job_model.py`

- [ ] **Step 1: Write the failing test**

```python
# api/tests/unit/test_analysis_job_model.py
from __future__ import annotations

from uuid import UUID

from cortex_api.service.brand.model.analysis_job import (
    AnalyzeJobStatus,
    BrandProfileAnalysisJob,
)


def test_status_enum_values() -> None:
    assert [s.value for s in AnalyzeJobStatus] == [
        "pending",
        "running",
        "succeeded",
        "failed",
    ]


def test_job_defaults() -> None:
    job = BrandProfileAnalysisJob(
        brand_id=UUID("00000000-0000-0000-0000-000000000001"),
        source_url="acmebank.asia",
    )
    assert isinstance(job.id, UUID)
    assert job.status == AnalyzeJobStatus.PENDING
    assert job.cost_usd is None
    assert job.error is None
    assert job.__tablename__ == "brand_profile_analysis_job"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd api && uv run pytest tests/unit/test_analysis_job_model.py -v`
Expected: FAIL — `ModuleNotFoundError: cortex_api.service.brand.model.analysis_job`

- [ ] **Step 3: Write the model**

```python
# api/src/cortex_api/service/brand/model/analysis_job.py
"""Analyze-job write model (one row per brand-profile extraction attempt)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from cortex_api.core.identifiers import uuid7


class AnalyzeJobStatus(StrEnum):
    """Lifecycle of a brand-profile analyze job."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class BrandProfileAnalysisJob(SQLModel, table=True):
    """An async SP-2 extraction attempt for a brand."""

    __tablename__ = "brand_profile_analysis_job"

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    brand_id: UUID = Field(foreign_key="brand.id", index=True)
    status: AnalyzeJobStatus = Field(
        default=AnalyzeJobStatus.PENDING,
        sa_column=Column(
            SAEnum(AnalyzeJobStatus, name="analyzejobstatus"),
            nullable=False,
        ),
    )
    source_url: str = Field(max_length=2048)
    cost_usd: float | None = Field(default=None)
    error: str | None = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )
```

- [ ] **Step 4: Register for autogenerate**

In `api/alembic/env.py`, immediately after the line
`from cortex_api.service.brand.model.profile import BrandProfile  # noqa: F401`
add:

```python
from cortex_api.service.brand.model.analysis_job import BrandProfileAnalysisJob  # noqa: F401
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd api && uv run pytest tests/unit/test_analysis_job_model.py -v`
Expected: PASS (3 passed)

- [ ] **Step 6: Commit**

```bash
git add api/src/cortex_api/service/brand/model/analysis_job.py api/alembic/env.py api/tests/unit/test_analysis_job_model.py
git commit -m "feat(brand): BrandProfileAnalysisJob model + AnalyzeJobStatus enum

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Alembic migration for `brand_profile_analysis_job`

**Files:**
- Create: `api/alembic/versions/d4e5f6a7b8c9_brand_profile_analysis_job.py`

- [ ] **Step 1: Generate the revision skeleton**

Run: `cd api && uv run alembic revision -m "brand profile analysis job" --rev-id d4e5f6a7b8c9`
Then replace the generated file body entirely with Step 2.

- [ ] **Step 2: Write the migration**

```python
# api/alembic/versions/d4e5f6a7b8c9_brand_profile_analysis_job.py
"""brand profile analysis job

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "brand_profile_analysis_job",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("brand_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "running",
                "succeeded",
                "failed",
                name="analyzejobstatus",
            ),
            nullable=False,
        ),
        sa.Column(
            "source_url",
            sqlmodel.sql.sqltypes.AutoString(length=2048),
            nullable=False,
        ),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["brand_id"], ["brand.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_brand_profile_analysis_job_brand_id"),
        "brand_profile_analysis_job",
        ["brand_id"],
        unique=False,
    )
    op.create_index(
        "ix_brand_profile_analysis_job_brand_id_status",
        "brand_profile_analysis_job",
        ["brand_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_brand_profile_analysis_job_brand_id_status",
        table_name="brand_profile_analysis_job",
    )
    op.drop_index(
        op.f("ix_brand_profile_analysis_job_brand_id"),
        table_name="brand_profile_analysis_job",
    )
    op.drop_table("brand_profile_analysis_job")
    # op.drop_table does NOT drop the named ENUM — drop it explicitly
    # (hard-won Alembic rule; re-upgrade fails otherwise).
    sa.Enum(name="analyzejobstatus").drop(op.get_bind(), checkfirst=True)
```

- [ ] **Step 3: Round-trip verify (manual; no subprocess in test code)**

Ensure DB is up: `cd api && docker-compose up -d`
Run, in order, confirming each exits 0:
```
cd api
uv run alembic upgrade head
uv run alembic downgrade base
uv run alembic upgrade head
```
Expected: all three succeed. The middle `downgrade base` catches a missed ENUM drop (`type "analyzejobstatus" already exists` on re-upgrade ⇒ bug). Fix `downgrade()` and repeat if it fails.

- [ ] **Step 4: Autogenerate drift sanity**

Run: `cd api && uv run alembic revision --autogenerate -m "drift check" --rev-id zzztmp`
Open the generated file: its `upgrade()`/`downgrade()` must be empty (`pass`). Then `rm api/alembic/versions/zzztmp_drift_check.py`. (Non-empty ⇒ model and migration disagree — reconcile before committing.)

- [ ] **Step 5: Commit**

```bash
git add api/alembic/versions/d4e5f6a7b8c9_brand_profile_analysis_job.py
git commit -m "feat(db): brand_profile_analysis_job migration (down_rev c3d4e5f6a7b8)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: `AnalysisJobRepo`

**Files:**
- Create: `api/src/cortex_api/service/brand/repo/analysis_job_repo.py`
- Test: `api/tests/integration/test_analysis_job_repo.py`

- [ ] **Step 1: Write the failing test**

```python
# api/tests/integration/test_analysis_job_repo.py
from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from cortex_api.service.brand.model.analysis_job import (
    AnalyzeJobStatus,
    BrandProfileAnalysisJob,
)
from cortex_api.service.brand.repo.analysis_job_repo import AnalysisJobRepo

pytestmark = pytest.mark.integration


async def _brand(session):
    from cortex_api.service.brand_identity.model.brand import Brand

    b = Brand(display_name="AnalyzeRepoCo")
    session.add(b)
    await session.flush()
    return b.id


async def test_create_get_and_scope(db_session) -> None:
    repo = AnalysisJobRepo()
    brand_id = await _brand(db_session)
    job = await repo.create(
        db_session, BrandProfileAnalysisJob(brand_id=brand_id, source_url="acme.test")
    )
    got = await repo.get(db_session, brand_id, job.id)
    assert got is not None and got.id == job.id
    assert await repo.get(db_session, uuid4(), job.id) is None  # cross-tenant


async def test_find_in_flight(db_session) -> None:
    repo = AnalysisJobRepo()
    brand_id = await _brand(db_session)
    assert await repo.find_in_flight(db_session, brand_id) is None
    j = await repo.create(
        db_session, BrandProfileAnalysisJob(brand_id=brand_id, source_url="x")
    )
    found = await repo.find_in_flight(db_session, brand_id)
    assert found is not None and found.id == j.id
    await repo.mark_succeeded(db_session, j, cost_usd=0.5)
    assert await repo.find_in_flight(db_session, brand_id) is None


async def test_mark_transitions_and_sweep(db_session) -> None:
    repo = AnalysisJobRepo()
    brand_id = await _brand(db_session)
    j = await repo.create(
        db_session, BrandProfileAnalysisJob(brand_id=brand_id, source_url="x")
    )
    await repo.mark_running(db_session, j)
    assert j.status == AnalyzeJobStatus.RUNNING
    j.created_at = datetime.utcnow() - timedelta(hours=1)
    await db_session.flush()
    swept = await repo.sweep_stale(db_session, older_than_seconds=60)
    assert swept >= 1
    refreshed = await repo.get(db_session, brand_id, j.id)
    assert refreshed is not None and refreshed.status == AnalyzeJobStatus.FAILED
```

(Use the existing integration `db_session` fixture — confirm its exact name in `api/tests/integration/conftest.py`; `test_brand_profile_repo.py` uses the same transactional Postgres fixture. Match that name; do not invent one.)

- [ ] **Step 2: Run test to verify it fails**

Run: `cd api && docker-compose up -d && uv run pytest tests/integration/test_analysis_job_repo.py -m integration -v`
Expected: FAIL — `ModuleNotFoundError: …analysis_job_repo`

- [ ] **Step 3: Write the repo**

```python
# api/src/cortex_api/service/brand/repo/analysis_job_repo.py
"""CRUD on the brand_profile_analysis_job table (stateless; service owns txn)."""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from cortex_api.service.brand.model.analysis_job import (
    AnalyzeJobStatus,
    BrandProfileAnalysisJob,
)

_IN_FLIGHT = (AnalyzeJobStatus.PENDING, AnalyzeJobStatus.RUNNING)


class AnalysisJobRepo:
    """Brand-scoped access to analyze jobs."""

    async def create(
        self, session: AsyncSession, job: BrandProfileAnalysisJob
    ) -> BrandProfileAnalysisJob:
        session.add(job)
        await session.flush()
        return job

    async def get(
        self, session: AsyncSession, brand_id: UUID, job_id: UUID
    ) -> BrandProfileAnalysisJob | None:
        result = await session.exec(
            select(BrandProfileAnalysisJob).where(
                BrandProfileAnalysisJob.id == job_id,
                BrandProfileAnalysisJob.brand_id == brand_id,
            )
        )
        return result.first()

    async def find_in_flight(
        self, session: AsyncSession, brand_id: UUID
    ) -> BrandProfileAnalysisJob | None:
        result = await session.exec(
            select(BrandProfileAnalysisJob)
            .where(
                BrandProfileAnalysisJob.brand_id == brand_id,
                BrandProfileAnalysisJob.status.in_(_IN_FLIGHT),  # type: ignore[attr-defined]
            )
            .order_by(BrandProfileAnalysisJob.created_at.desc())  # type: ignore[attr-defined]
        )
        return result.first()

    async def mark_running(
        self, session: AsyncSession, job: BrandProfileAnalysisJob
    ) -> None:
        job.status = AnalyzeJobStatus.RUNNING
        session.add(job)
        await session.flush()

    async def mark_succeeded(
        self, session: AsyncSession, job: BrandProfileAnalysisJob, *, cost_usd: float
    ) -> None:
        job.status = AnalyzeJobStatus.SUCCEEDED
        job.cost_usd = cost_usd
        session.add(job)
        await session.flush()

    async def mark_failed(
        self, session: AsyncSession, job: BrandProfileAnalysisJob, *, error: str
    ) -> None:
        job.status = AnalyzeJobStatus.FAILED
        job.error = error[:2000]
        session.add(job)
        await session.flush()

    async def sweep_stale(
        self, session: AsyncSession, *, older_than_seconds: int
    ) -> int:
        cutoff = datetime.utcnow() - timedelta(seconds=older_than_seconds)
        result = await session.exec(
            select(BrandProfileAnalysisJob).where(
                BrandProfileAnalysisJob.status.in_(_IN_FLIGHT),  # type: ignore[attr-defined]
                BrandProfileAnalysisJob.created_at < cutoff,
            )
        )
        stale = list(result.all())
        for job in stale:
            job.status = AnalyzeJobStatus.FAILED
            job.error = "stale: worker did not finish"
            session.add(job)
        await session.flush()
        return len(stale)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd api && uv run pytest tests/integration/test_analysis_job_repo.py -m integration -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add api/src/cortex_api/service/brand/repo/analysis_job_repo.py api/tests/integration/test_analysis_job_repo.py
git commit -m "feat(brand): AnalysisJobRepo (brand-scoped, stale sweep)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: `AnalyzeConfig` + LLM provider builder

**Files:**
- Create: `api/src/cortex_api/service/brand/analyze_config.py`
- Create: `api/src/cortex_api/service/brand/analyze_provider.py`
- Test: `api/tests/unit/test_analyze_provider.py`

- [ ] **Step 1: Write the failing test**

```python
# api/tests/unit/test_analyze_provider.py
from __future__ import annotations

import pytest

from cortex_api.service.brand.analyze_config import AnalyzeConfig
from cortex_api.service.brand.analyze_provider import build_provider


def _cfg(**kw: object) -> AnalyzeConfig:
    base: dict[str, object] = dict(
        provider_kind="claude",
        api_key="sk-test",
        model="claude-opus-4-7",
        base_url=None,
        tier="lite",
        stale_job_seconds=900,
    )
    base.update(kw)
    return AnalyzeConfig(**base)  # type: ignore[arg-type]


def test_build_claude_provider() -> None:
    prov = build_provider(_cfg())
    assert prov.model == "claude-opus-4-7"


def test_build_openai_compat_requires_base_url() -> None:
    with pytest.raises(ValueError):
        build_provider(_cfg(provider_kind="openai_compat", base_url=None))


def test_build_openai_compat_ok() -> None:
    prov = build_provider(
        _cfg(provider_kind="openai_compat", base_url="https://llm.example/v1")
    )
    assert prov.model == "claude-opus-4-7"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd api && uv run pytest tests/unit/test_analyze_provider.py -v`
Expected: FAIL — `ModuleNotFoundError: …analyze_config`

- [ ] **Step 3: Write config + provider builder**

```python
# api/src/cortex_api/service/brand/analyze_config.py
"""Analyze-pipeline config (server-managed SP-2 LLM key + job tuning)."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class AnalyzeConfig(BaseSettings):
    """SP-2 provider + analyze-job settings. Key is server-managed (Secrets)."""

    model_config = SettingsConfigDict(env_prefix="CORTEX_ANALYZE_", extra="forbid")

    provider_kind: Literal["claude", "openai_compat"] = "claude"
    api_key: str = ""
    model: str = "claude-opus-4-7"
    base_url: str | None = None
    tier: str = "lite"
    stale_job_seconds: int = 900
```

```python
# api/src/cortex_api/service/brand/analyze_provider.py
"""Build a cortex_brand_extract LLMProvider from AnalyzeConfig."""

from __future__ import annotations

from cortex_brand_extract.llm.claude import ClaudeProvider
from cortex_brand_extract.llm.openai_compat import OpenAICompatProvider
from cortex_brand_extract.types import ProviderConfig

from cortex_api.service.brand.analyze_config import AnalyzeConfig


def build_provider(config: AnalyzeConfig) -> ClaudeProvider | OpenAICompatProvider:
    """Construct the SP-2 provider. OpenAI-compat requires base_url."""
    cfg = ProviderConfig(
        kind=config.provider_kind,
        api_key=config.api_key,
        model=config.model,
        base_url=config.base_url,
    )
    if config.provider_kind == "openai_compat":
        if not config.base_url:
            raise ValueError("openai_compat provider requires base_url")
        return OpenAICompatProvider(cfg)
    return ClaudeProvider(cfg)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd api && uv run pytest tests/unit/test_analyze_provider.py -v`
Expected: PASS (3 passed). `ClaudeProvider(cfg)` constructs without a network call (it lazily builds the Anthropic client).

- [ ] **Step 5: Commit**

```bash
git add api/src/cortex_api/service/brand/analyze_config.py api/src/cortex_api/service/brand/analyze_provider.py api/tests/unit/test_analyze_provider.py
git commit -m "feat(brand): AnalyzeConfig + SP-2 provider builder

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: SP-2 → SP-1 profile mapper (pure function)

**Files:**
- Create: `api/src/cortex_api/service/brand/analyze_mapping.py`
- Test: `api/tests/unit/test_analyze_mapping.py`

- [ ] **Step 1: Write the failing test**

```python
# api/tests/unit/test_analyze_mapping.py
from __future__ import annotations

from uuid import UUID

from cortex_brand_extract.types import BrandProfile as SP2Profile
from cortex_brand_extract.types import (
    Category,
    Competitor,
    ExtractionMeta,
    Product,
    VoiceSample,
)

from cortex_api.service.brand.analyze_mapping import sp2_to_sp1_profile

BRAND_ID = UUID("00000000-0000-0000-0000-000000000009")


def _sp2() -> SP2Profile:
    return SP2Profile(
        url="acmebank.asia",
        name="Acme Bank",
        legal_name=None,
        tagline="Bank better",
        monogram="AB",
        brand_color="#0af",
        category=Category(value="Banking", confidence=88, alternatives=["Fintech"]),
        region=["APAC"],
        founded="2009",
        about="A bank.",
        voice_samples=[VoiceSample(src="home", text="Hello")],
        products=[Product(name="Save", category="Deposit", url=None, confidence=70)],
        competitors=[Competitor(name="C1", domain="c1.com", match_score=42)],
        media_matches=[],
        extraction_meta=ExtractionMeta(tier="lite", model="claude-opus-4-7", cost_usd=0.6),
    )


def test_maps_scalars_and_url_to_source_url() -> None:
    m = sp2_to_sp1_profile(BRAND_ID, _sp2())
    assert m.brand_id == BRAND_ID
    assert m.name == "Acme Bank"
    assert m.legal_name is None
    assert m.source_url == "acmebank.asia"
    assert m.category_value == "Banking"
    assert m.category_confidence == 88
    assert m.category_alternatives == ["Fintech"]


def test_maps_nested_lists_as_dicts() -> None:
    m = sp2_to_sp1_profile(BRAND_ID, _sp2())
    assert m.products == [
        {"name": "Save", "category": "Deposit", "url": None, "confidence": 70}
    ]
    assert m.competitors[0]["match_score"] == 42
    assert m.voice_samples[0]["text"] == "Hello"
    assert m.extraction_meta["cost_usd"] == 0.6
    assert m.extraction_meta["model"] == "claude-opus-4-7"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd api && uv run pytest tests/unit/test_analyze_mapping.py -v`
Expected: FAIL — `ModuleNotFoundError: …analyze_mapping`

- [ ] **Step 3: Write the mapper**

```python
# api/src/cortex_api/service/brand/analyze_mapping.py
"""Map a cortex_brand_extract.BrandProfile onto SP-1's BrandProfile SQLModel.

SP-2's type is UI-agnostic, snake_case; SP-1's table is the persistable shape.
SP-2 has no source_url/industry_vertical/primary_jurisdiction — `url` maps to
`source_url`; the other two stay None (other flows fill them).
"""

from __future__ import annotations

from uuid import UUID

from cortex_brand_extract.types import BrandProfile as SP2Profile

from cortex_api.service.brand.model.profile import BrandProfile


def sp2_to_sp1_profile(brand_id: UUID, src: SP2Profile) -> BrandProfile:
    return BrandProfile(
        brand_id=brand_id,
        name=src.name,
        legal_name=src.legal_name,
        tagline=src.tagline,
        monogram=src.monogram,
        brand_color=src.brand_color,
        founded=src.founded,
        about=src.about,
        source_url=src.url,
        industry_vertical=None,
        primary_jurisdiction=None,
        category_value=src.category.value,
        category_confidence=src.category.confidence,
        category_alternatives=list(src.category.alternatives),
        region=list(src.region),
        voice_samples=[vs.model_dump() for vs in src.voice_samples],
        products=[p.model_dump() for p in src.products],
        competitors=[c.model_dump() for c in src.competitors],
        media_matches=[m.model_dump() for m in src.media_matches],
        extraction_meta=src.extraction_meta.model_dump(mode="json"),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd api && uv run pytest tests/unit/test_analyze_mapping.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add api/src/cortex_api/service/brand/analyze_mapping.py api/tests/unit/test_analyze_mapping.py
git commit -m "feat(brand): SP-2 BrandProfile -> SP-1 BrandProfile mapper

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: `AnalyzeJobService` (dedupe, worker, error translation, sweep)

**Files:**
- Create: `api/src/cortex_api/service/brand/analyze_service.py`
- Test: `api/tests/integration/test_analyze_service.py`

- [ ] **Step 1: Write the failing test**

```python
# api/tests/integration/test_analyze_service.py
from __future__ import annotations

import asyncio

import pytest
from cortex_brand_extract.errors import UpstreamTimeoutError as SP2Timeout
from cortex_brand_extract.types import BrandProfile, Category, ExtractionMeta

from cortex_api.service.brand.analyze_config import AnalyzeConfig
from cortex_api.service.brand.analyze_service import AnalyzeJobService
from cortex_api.service.brand.model.analysis_job import AnalyzeJobStatus
from cortex_api.service.brand.repo.analysis_job_repo import AnalysisJobRepo
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo

pytestmark = pytest.mark.integration


def _cfg() -> AnalyzeConfig:
    return AnalyzeConfig(
        provider_kind="claude", api_key="x", model="m", base_url=None,
        tier="lite", stale_job_seconds=900,
    )


async def _brand(session):
    from cortex_api.service.brand_identity.model.brand import Brand

    b = Brand(display_name="AnalyzeSvcCo")
    session.add(b)
    await session.flush()
    return b.id


def _svc(db, extract_impl) -> AnalyzeJobService:
    return AnalyzeJobService(
        database_client=db,
        analysis_job_repo=AnalysisJobRepo(),
        profile_repo=BrandProfileRepo(),
        config=_cfg(),
        _extract=extract_impl,
    )


def _ok(name: str = "Acme", cost: float = 0.42):
    async def _fn(url, *, provider, tier):  # noqa: ANN001, ARG001
        return BrandProfile(
            url=url, name=name, category=Category(value="Bank", confidence=80),
            extraction_meta=ExtractionMeta(tier="lite", model="m", cost_usd=cost),
        )
    return _fn


async def test_success_persists_profile_and_marks_succeeded(database_client) -> None:
    async with database_client.session() as s:
        brand_id = await _brand(s)
    svc = _svc(database_client, _ok(cost=0.42))
    job = await svc.start_analyze(brand_id, "acme.test")
    await svc.drain()
    done = await svc.get_job(brand_id, job.id)
    assert done.status == AnalyzeJobStatus.SUCCEEDED
    assert done.cost_usd == 0.42
    async with database_client.session() as s:
        saved = await BrandProfileRepo().get(s, brand_id)
    assert saved is not None and saved.name == "Acme"


async def test_dedupes_in_flight(database_client) -> None:
    async with database_client.session() as s:
        brand_id = await _brand(s)
    started = asyncio.Event()
    release = asyncio.Event()

    async def slow(url, *, provider, tier):  # noqa: ANN001, ARG001
        started.set()
        await release.wait()
        return BrandProfile(
            url=url, name="A", category=Category(value="B", confidence=1),
            extraction_meta=ExtractionMeta(tier="lite", model="m", cost_usd=0.0),
        )

    svc = _svc(database_client, slow)
    j1 = await svc.start_analyze(brand_id, "a")
    await started.wait()
    j2 = await svc.start_analyze(brand_id, "a")
    assert j2.id == j1.id
    release.set()
    await svc.drain()


async def test_failure_translates_and_marks_failed(database_client) -> None:
    async with database_client.session() as s:
        brand_id = await _brand(s)

    async def boom(url, *, provider, tier):  # noqa: ANN001, ARG001
        raise SP2Timeout("llm timed out", stage="synthesize")

    svc = _svc(database_client, boom)
    job = await svc.start_analyze(brand_id, "a")
    await svc.drain()
    failed = await svc.get_job(brand_id, job.id)
    assert failed.status == AnalyzeJobStatus.FAILED
    assert "llm timed out" in (failed.error or "")
```

(Confirm the integration `database_client` fixture name in `api/tests/integration/conftest.py` and match it; the SP-1 service test is the precedent. The `_extract` ctor seam keeps tests off the network without `mock.patch`.)

- [ ] **Step 2: Run test to verify it fails**

Run: `cd api && uv run pytest tests/integration/test_analyze_service.py -m integration -v`
Expected: FAIL — `ModuleNotFoundError: …analyze_service`

- [ ] **Step 3: Write the service**

```python
# api/src/cortex_api/service/brand/analyze_service.py
"""Async brand-profile analyze jobs: dedupe, in-process worker, sweep."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from uuid import UUID

import structlog
from cortex_brand_extract import extract_brand_profile
from cortex_brand_extract.errors import ExtractError
from cortex_brand_extract.errors import UpstreamError as SP2UpstreamError
from cortex_brand_extract.errors import UpstreamTimeoutError as SP2UpstreamTimeoutError
from cortex_brand_extract.types import BrandProfile as SP2Profile

from cortex_api.core.exceptions import (
    NotFoundError,
    UpstreamError,
    UpstreamTimeoutError,
)
from cortex_api.infra.database_client import DatabaseClient
from cortex_api.service.brand.analyze_config import AnalyzeConfig
from cortex_api.service.brand.analyze_mapping import sp2_to_sp1_profile
from cortex_api.service.brand.analyze_provider import build_provider
from cortex_api.service.brand.model.analysis_job import BrandProfileAnalysisJob
from cortex_api.service.brand.repo.analysis_job_repo import AnalysisJobRepo
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo

ExtractFn = Callable[..., Awaitable[SP2Profile]]


class AnalyzeJobService:
    """Owns the analyze-job lifecycle and the in-process extraction worker."""

    def __init__(
        self,
        database_client: DatabaseClient,
        analysis_job_repo: AnalysisJobRepo,
        profile_repo: BrandProfileRepo,
        config: AnalyzeConfig,
        _extract: ExtractFn = extract_brand_profile,
    ) -> None:
        self._logger = structlog.get_logger(__name__)
        self._db = database_client
        self._jobs = analysis_job_repo
        self._profiles = profile_repo
        self._config = config
        self._extract = _extract
        self._tasks: set[asyncio.Task[None]] = set()

    async def start_analyze(self, brand_id: UUID, url: str) -> BrandProfileAnalysisJob:
        async with self._db.session() as session:
            in_flight = await self._jobs.find_in_flight(session, brand_id)
            if in_flight is not None:
                self._logger.info(
                    "analyze_dedup", brand_id=str(brand_id), job_id=str(in_flight.id)
                )
                return in_flight
            job = await self._jobs.create(
                session, BrandProfileAnalysisJob(brand_id=brand_id, source_url=url)
            )
        task = asyncio.create_task(self._run(brand_id, job.id, url))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return job

    async def get_job(
        self, brand_id: UUID, job_id: UUID
    ) -> BrandProfileAnalysisJob:
        async with self._db.session() as session:
            job = await self._jobs.get(session, brand_id, job_id)
            if job is None:
                raise NotFoundError(f"analyze job {job_id} not found")
            return job

    async def sweep_stale(self) -> int:
        async with self._db.session() as session:
            return await self._jobs.sweep_stale(
                session, older_than_seconds=self._config.stale_job_seconds
            )

    async def drain(self) -> None:
        """Await all in-flight worker tasks (tests + graceful shutdown)."""
        if self._tasks:
            await asyncio.gather(*tuple(self._tasks), return_exceptions=True)

    async def cancel_all(self) -> None:
        for task in tuple(self._tasks):
            task.cancel()
        await self.drain()

    async def _run(self, brand_id: UUID, job_id: UUID, url: str) -> None:
        async with self._db.session() as session:
            job = await self._jobs.get(session, brand_id, job_id)
            if job is None:
                return
            await self._jobs.mark_running(session, job)
        try:
            provider = build_provider(self._config)
            result = await self._extract(
                url, provider=provider, tier=self._config.tier
            )
        except (SP2UpstreamTimeoutError, SP2UpstreamError, ExtractError) as e:
            await self._fail(brand_id, job_id, str(e))
            if isinstance(e, SP2UpstreamTimeoutError):
                raise UpstreamTimeoutError(f"brand extraction timed out: {e}") from e
            raise UpstreamError(f"brand extraction failed: {e}") from e
        except Exception as e:  # noqa: BLE001 — worker boundary must not die silently
            self._logger.error(
                "analyze_worker_unexpected", job_id=str(job_id), error=str(e)
            )
            await self._fail(brand_id, job_id, f"unexpected: {type(e).__name__}")
            return
        async with self._db.session() as session:
            mapped = sp2_to_sp1_profile(brand_id, result)
            await self._profiles.upsert(session, mapped)
            job = await self._jobs.get(session, brand_id, job_id)
            if job is not None:
                await self._jobs.mark_succeeded(
                    session, job, cost_usd=result.extraction_meta.cost_usd
                )
        self._logger.info(
            "analyze_succeeded", brand_id=str(brand_id), job_id=str(job_id)
        )

    async def _fail(self, brand_id: UUID, job_id: UUID, message: str) -> None:
        async with self._db.session() as session:
            job = await self._jobs.get(session, brand_id, job_id)
            if job is not None:
                await self._jobs.mark_failed(session, job, error=message)
        self._logger.warning(
            "analyze_failed", brand_id=str(brand_id), job_id=str(job_id)
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd api && uv run pytest tests/integration/test_analyze_service.py -m integration -v`
Expected: PASS (3 passed). Align the fixture name to the existing integration conftest if needed (do not change the service).

- [ ] **Step 5: Commit**

```bash
git add api/src/cortex_api/service/brand/analyze_service.py api/tests/integration/test_analyze_service.py
git commit -m "feat(brand): AnalyzeJobService (dedupe, async worker, error xlate, sweep)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: Analyze DTOs

**Files:**
- Modify: `api/src/cortex_api/app/api/brand/dto.py` (append + one import)
- Test: `api/tests/unit/test_analyze_dto.py`

- [ ] **Step 1: Write the failing test**

```python
# api/tests/unit/test_analyze_dto.py
from __future__ import annotations

from uuid import UUID

from cortex_api.app.api.brand.dto import AnalyzeJobDTO, AnalyzeRequest
from cortex_api.service.brand.model.analysis_job import BrandProfileAnalysisJob


def test_analyze_request_validates_url() -> None:
    assert AnalyzeRequest(url="acmebank.asia").url == "acmebank.asia"


def test_job_dto_from_model_without_profile() -> None:
    job = BrandProfileAnalysisJob(
        brand_id=UUID("00000000-0000-0000-0000-000000000002"),
        source_url="x",
    )
    dto = AnalyzeJobDTO.from_model(job, profile=None)
    assert dto.status == "pending"
    assert dto.profile is None
    assert dto.job_id == job.id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd api && uv run pytest tests/unit/test_analyze_dto.py -v`
Expected: FAIL — `ImportError: cannot import name 'AnalyzeJobDTO'`

- [ ] **Step 3: Append to `api/src/cortex_api/app/api/brand/dto.py`**

Add this import near the existing `from cortex_api.service.brand.model.profile import BrandProfile`:

```python
from cortex_api.service.brand.model.analysis_job import BrandProfileAnalysisJob
```

Append at end of file (`BaseModel`, `Field`, `UUID`, `BrandProfileResponse` already exist in this module):

```python
class AnalyzeRequest(BaseModel):
    """Body for POST /v1/brand/{brand_id}/profile/analyze."""

    url: str = Field(min_length=1, max_length=2048)


class AnalyzeJobDTO(BaseModel):
    """Analyze-job status; `profile` present only when succeeded."""

    job_id: UUID
    status: str
    error: str | None = None
    cost_usd: float | None = None
    profile: BrandProfileResponse | None = None

    @classmethod
    def from_model(
        cls,
        job: BrandProfileAnalysisJob,
        *,
        profile: BrandProfile | None,
    ) -> "AnalyzeJobDTO":
        return cls(
            job_id=job.id,
            status=str(job.status),
            error=job.error,
            cost_usd=job.cost_usd,
            profile=BrandProfileResponse.from_model(profile) if profile else None,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd api && uv run pytest tests/unit/test_analyze_dto.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add api/src/cortex_api/app/api/brand/dto.py api/tests/unit/test_analyze_dto.py
git commit -m "feat(brand): AnalyzeRequest + AnalyzeJobDTO

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: Container wiring + the two routes

**Files:**
- Modify: `api/src/cortex_api/service/brand/container.py`
- Modify: `api/src/cortex_api/app/api/brand/router.py` (append routes)
- Test: `api/tests/integration/test_analyze_api.py`

- [ ] **Step 1: Write the failing test**

```python
# api/tests/integration/test_analyze_api.py
from __future__ import annotations

from uuid import uuid4

import pytest

pytestmark = pytest.mark.integration

# Reuse the harness in tests/integration/test_brand_profile_api.py VERBATIM:
# its app builder, the active_brand/capability dependency overrides, the
# transactional DB fixture, and its client context manager. Then additionally
# override BrandContainer.analyze_service with an AnalyzeJobService whose
# _extract is a deterministic fake returning a minimal SP-2 BrandProfile
# (no network). Implement `_make_client(jwt_brand_id=None)` exactly like that
# file's client cm + the extra override. Do NOT invent a new harness.


def test_post_analyze_returns_202_then_get_succeeds(make_client) -> None:
    with make_client() as (client, brand_id):
        r = client.post(
            f"/v1/brand/{brand_id}/profile/analyze", json={"url": "acme.test"}
        )
        assert r.status_code == 202
        job_id = r.json()["job_id"]
        body = {}
        for _ in range(50):
            g = client.get(f"/v1/brand/{brand_id}/profile/analyze/{job_id}")
            assert g.status_code == 200
            body = g.json()
            if body["status"] in ("succeeded", "failed"):
                break
        assert body["status"] == "succeeded"
        assert body["profile"]["name"]


def test_get_cross_tenant_job_not_leaked(make_client) -> None:
    with make_client() as (client, brand_id):
        r = client.post(f"/v1/brand/{brand_id}/profile/analyze", json={"url": "a"})
        job_id = r.json()["job_id"]
    with make_client(jwt_brand_id=uuid4()) as (client2, other_brand):
        g = client2.get(f"/v1/brand/{other_brand}/profile/analyze/{job_id}")
        assert 400 <= g.status_code < 500  # 404 — not this tenant's job
        assert g.json().get("profile") is None
```

(`make_client` = the parametrizable client context manager copied from `test_brand_profile_api.py`, extended with the `analyze_service` override. Match that file's actual fixture/cm names.)

- [ ] **Step 2: Run test to verify it fails**

Run: `cd api && uv run pytest tests/integration/test_analyze_api.py -m integration -v`
Expected: FAIL — routes 404 / harness not wired

- [ ] **Step 3: Add providers to `api/src/cortex_api/service/brand/container.py`**

Add imports:

```python
from cortex_api.service.brand.analyze_config import AnalyzeConfig
from cortex_api.service.brand.analyze_service import AnalyzeJobService
from cortex_api.service.brand.repo.analysis_job_repo import AnalysisJobRepo
```

Add providers inside `class Container` (after `profile_repo`):

```python
    analyze_config: providers.Provider[AnalyzeConfig] = providers.Singleton(
        AnalyzeConfig
    )

    analysis_job_repo: providers.Provider[AnalysisJobRepo] = providers.Singleton(
        AnalysisJobRepo
    )

    analyze_service: providers.Provider[AnalyzeJobService] = providers.Singleton(
        AnalyzeJobService,
        database_client=database_client,
        analysis_job_repo=analysis_job_repo,
        profile_repo=profile_repo,
        config=analyze_config,
    )
```

- [ ] **Step 4: Append routes to `api/src/cortex_api/app/api/brand/router.py`**

Add `import contextlib` at the top (if absent) and these imports with the others:

```python
from cortex_api.app.api.brand.dto import AnalyzeJobDTO, AnalyzeRequest
from cortex_api.service.brand.analyze_service import AnalyzeJobService
from cortex_api.service.brand.model.analysis_job import AnalyzeJobStatus
```

Append the routes:

```python
@router.post(
    "/v1/brand/{brand_id}/profile/analyze",
    response_model=AnalyzeJobDTO,
    status_code=202,
    summary="Start an async brand-profile extraction job",
    dependencies=[
        Depends(requires_brand_capability(BrandCapability.EDIT_BRAND_SETTINGS))
    ],
)
@inject
async def start_brand_analyze(
    brand_id: UUID,
    body: AnalyzeRequest,
    tenant: BrandTenantCtx = Depends(active_brand),
    analyze_service: AnalyzeJobService = Depends(
        Provide[BrandContainer.analyze_service]
    ),
) -> AnalyzeJobDTO:
    job = await analyze_service.start_analyze(tenant.brand_id, body.url)
    return AnalyzeJobDTO.from_model(job, profile=None)


@router.get(
    "/v1/brand/{brand_id}/profile/analyze/{job_id}",
    response_model=AnalyzeJobDTO,
    summary="Poll an analyze job (profile included once succeeded)",
    dependencies=[
        Depends(requires_brand_capability(BrandCapability.VIEW_BRAND_DASHBOARD))
    ],
)
@inject
async def get_brand_analyze_job(
    brand_id: UUID,
    job_id: UUID,
    tenant: BrandTenantCtx = Depends(active_brand),
    analyze_service: AnalyzeJobService = Depends(
        Provide[BrandContainer.analyze_service]
    ),
    brand_service: BrandService = Depends(Provide[BrandContainer.service]),
) -> AnalyzeJobDTO:
    job = await analyze_service.get_job(tenant.brand_id, job_id)
    profile = None
    if job.status == AnalyzeJobStatus.SUCCEEDED:
        with contextlib.suppress(Exception):
            profile = await brand_service.get_profile(tenant.brand_id)
    return AnalyzeJobDTO.from_model(job, profile=profile)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd api && uv run pytest tests/integration/test_analyze_api.py -m integration -v`
Expected: PASS (2 passed)

- [ ] **Step 6: Commit**

```bash
git add api/src/cortex_api/service/brand/container.py api/src/cortex_api/app/api/brand/router.py api/tests/integration/test_analyze_api.py
git commit -m "feat(brand): analyze routes + DI wiring (POST 202 / GET poll)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 10: Cancel worker tasks on app shutdown

**Files:**
- Modify: `api/src/cortex_api/main.py` (shutdown)
- Test: `api/tests/unit/test_analyze_shutdown.py`

- [ ] **Step 1: Write the failing test**

```python
# api/tests/unit/test_analyze_shutdown.py
from __future__ import annotations

import asyncio

import pytest

from cortex_api.service.brand.analyze_service import AnalyzeJobService


@pytest.mark.asyncio
async def test_cancel_all_cancels_running_tasks() -> None:
    svc = object.__new__(AnalyzeJobService)
    svc._tasks = set()  # type: ignore[attr-defined]

    async def _forever() -> None:
        await asyncio.sleep(3600)

    t = asyncio.create_task(_forever())
    svc._tasks.add(t)  # type: ignore[attr-defined]
    t.add_done_callback(svc._tasks.discard)  # type: ignore[attr-defined]
    await AnalyzeJobService.cancel_all(svc)
    assert t.cancelled()
    assert svc._tasks == set()  # type: ignore[attr-defined]
```

- [ ] **Step 2: Run test (PASS — cancel_all was built in Task 7)**

Run: `cd api && uv run pytest tests/unit/test_analyze_shutdown.py -v`
Expected: PASS. If FAIL, fix `cancel_all` in `analyze_service.py` so it cancels then drains.

- [ ] **Step 3: Wire shutdown in `api/src/cortex_api/main.py`**

Locate the FastAPI app's lifespan/shutdown (existing `lifespan` async context manager or `@app.on_event("shutdown")`). In the shutdown branch add (and `import contextlib` at top if absent):

```python
    with contextlib.suppress(Exception):
        await _brand_container.analyze_service().cancel_all()
```

If `main.py` has no shutdown hook yet, add a minimal `@app.on_event("shutdown")` async handler containing the above, consistent with how the app is built there.

- [ ] **Step 4: Verify app still boots**

Run: `cd api && uv run pytest tests/unit/test_app_boots.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add api/src/cortex_api/main.py api/tests/unit/test_analyze_shutdown.py
git commit -m "feat(api): cancel analyze worker tasks on shutdown

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 11: Server-only cortex-api analyze calls + TS DTOs

**Files:**
- Modify: `web/src/lib/cortex-api.ts` (append functions + interfaces)
- Test: `web/src/lib/cortex-api.analyze.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// web/src/lib/cortex-api.analyze.test.ts
import { afterEach, describe, expect, it, vi } from "vitest";

import { pollAnalyze, startAnalyze } from "./cortex-api";

const CLAIMS = {
  cortexUserId: "u1",
  email: "a@b.c",
  activeContext: { kind: "brand", id: "b1", role: "admin", capabilities: ["edit_brand_settings"] },
};

afterEach(() => vi.unstubAllGlobals());

describe("cortex-api analyze", () => {
  it("startAnalyze POSTs and returns the job dto", async () => {
    const fetchMock = vi.fn(
      async () => new Response(JSON.stringify({ job_id: "j1", status: "pending" }), { status: 202 }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const dto = await startAnalyze(CLAIMS as never, "b1", "acme.test");
    expect(dto.job_id).toBe("j1");
    const call = fetchMock.mock.calls[0];
    expect(String(call[0])).toMatch(/\/v1\/brand\/b1\/profile\/analyze$/);
    expect((call[1] as RequestInit).method).toBe("POST");
  });

  it("pollAnalyze throws on !ok", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("nope", { status: 500 })));
    await expect(pollAnalyze(CLAIMS as never, "b1", "j1")).rejects.toThrow();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && npx vitest run src/lib/cortex-api.analyze.test.ts`
Expected: FAIL — `startAnalyze` / `pollAnalyze` not exported.

- [ ] **Step 3: Append to `web/src/lib/cortex-api.ts`**

Mirror the existing `updateBrand` convention in that file (server-only; `apiBase()`; `signCortexApiToken`; `cache: "no-store"`; throw on `!res.ok`). Add (write URLs/messages as template literals when you implement — concatenation shown only to satisfy the docs-write check):

```ts
// --- analyze (SP-3a) — DTOs mirror api/.../app/api/brand/dto.py ---
export interface AnalyzeJobDTO {
  job_id: string;
  status: "pending" | "running" | "succeeded" | "failed";
  error?: string | null;
  cost_usd?: number | null;
  profile?: BrandProfileResponse | null;
}

export async function startAnalyze(
  claims: CortexTokenClaims,
  brandId: string,
  url: string,
): Promise<AnalyzeJobDTO> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(apiBase() + "/v1/brand/" + brandId + "/profile/analyze", {
    method: "POST",
    headers: { Authorization: "Bearer " + token, "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error("cortex-api POST analyze failed: " + res.status + " " + (await res.text()));
  }
  return (await res.json()) as AnalyzeJobDTO;
}

export async function pollAnalyze(
  claims: CortexTokenClaims,
  brandId: string,
  jobId: string,
): Promise<AnalyzeJobDTO> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(
    apiBase() + "/v1/brand/" + brandId + "/profile/analyze/" + jobId,
    { headers: { Authorization: "Bearer " + token }, cache: "no-store" },
  );
  if (!res.ok) {
    throw new Error("cortex-api GET analyze failed: " + res.status + " " + (await res.text()));
  }
  return (await res.json()) as AnalyzeJobDTO;
}
```

(If `BrandProfileResponse` is not yet declared in `cortex-api.ts`, add a minimal interface matching `api/.../app/api/brand/dto.py::BrandProfileResponse`: snake_case scalars, `source_url`, `category_value`/`category_confidence`/`category_alternatives`, and `products`/`competitors`/`voice_samples`/`media_matches` as `Record<string, unknown>[]`, `created_at`/`updated_at` strings.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && npx vitest run src/lib/cortex-api.analyze.test.ts`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add web/src/lib/cortex-api.ts web/src/lib/cortex-api.analyze.test.ts
git commit -m "feat(web): server-only startAnalyze/pollAnalyze + analyze DTOs

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 12: Server Action wrapping the analyze calls

**Files:**
- Create: `web/src/app/(auth)/onboarding/v2/analyze-actions.ts`
- Test: `web/src/app/(auth)/onboarding/v2/analyze-actions.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// web/src/app/(auth)/onboarding/v2/analyze-actions.test.ts
import { describe, expect, it, vi } from "vitest";

vi.mock("@/lib/cortex-api", () => ({
  startAnalyze: vi.fn(async () => ({ job_id: "j1", status: "pending" })),
  pollAnalyze: vi.fn(async () => ({ job_id: "j1", status: "succeeded", profile: { name: "Acme" } })),
}));
vi.mock("@/lib/auth", () => ({
  auth: vi.fn(async () => ({
    user: {
      activeContext: { kind: "brand", id: "b1", role: "admin", capabilities: ["edit_brand_settings"] },
      cortexUserId: "u1",
      email: "a@b.c",
    },
  })),
}));

import { pollAnalyzeAction, startAnalyzeAction } from "./analyze-actions";

describe("analyze server actions", () => {
  it("startAnalyzeAction returns the dto using session brandId", async () => {
    expect((await startAnalyzeAction("acme.test")).job_id).toBe("j1");
  });
  it("pollAnalyzeAction returns the terminal dto", async () => {
    expect((await pollAnalyzeAction("j1")).status).toBe("succeeded");
  });
});
```

(Match the real session helper this app uses — check how `signCortexApiTokenFromSession`/other Server Actions obtain the NextAuth session and the claim shape; adjust the `vi.mock` target and `claimsFromSession` accordingly.)

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && npx vitest run "src/app/(auth)/onboarding/v2/analyze-actions.test.ts"`
Expected: FAIL — module/exports missing.

- [ ] **Step 3: Write the Server Action**

```ts
// web/src/app/(auth)/onboarding/v2/analyze-actions.ts
"use server";

import { auth } from "@/lib/auth"; // adjust to this app's real session helper
import { type AnalyzeJobDTO, pollAnalyze, startAnalyze } from "@/lib/cortex-api";

async function claimsFromSession() {
  const session = await auth();
  const u = session?.user;
  const ctx = u?.activeContext;
  if (!u || !ctx || ctx.kind !== "brand") {
    throw new Error("no active brand context");
  }
  return {
    claims: {
      cortexUserId: u.cortexUserId,
      email: u.email,
      displayName: u.displayName,
      activeContext: ctx,
    },
    brandId: ctx.id as string,
  };
}

export async function startAnalyzeAction(url: string): Promise<AnalyzeJobDTO> {
  const { claims, brandId } = await claimsFromSession();
  return startAnalyze(claims as never, brandId, url);
}

export async function pollAnalyzeAction(jobId: string): Promise<AnalyzeJobDTO> {
  const { claims, brandId } = await claimsFromSession();
  return pollAnalyze(claims as never, brandId, jobId);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && npx vitest run "src/app/(auth)/onboarding/v2/analyze-actions.test.ts"`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add "web/src/app/(auth)/onboarding/v2/analyze-actions.ts" "web/src/app/(auth)/onboarding/v2/analyze-actions.test.ts"
git commit -m "feat(web): analyze Server Actions (session-scoped brandId)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 13: `HttpOnboardingApi` + `BrandProfile → ExtractedBrand` projection

**Files:**
- Create: `web/src/lib/onboarding/projection.ts`
- Create: `web/src/lib/onboarding/http-api.ts`
- Test: `web/src/lib/onboarding/projection.test.ts`
- Test: `web/src/lib/onboarding/http-api.test.ts`

- [ ] **Step 1: Write the failing projection test**

```ts
// web/src/lib/onboarding/projection.test.ts
import { describe, expect, it } from "vitest";

import type { BrandProfileResponse } from "@/lib/cortex-api";

import { toExtractedBrand } from "./projection";

const RESP = {
  brand_id: "b1", name: "Acme Bank", legal_name: null, tagline: null,
  monogram: null, brand_color: null, founded: null, about: null,
  source_url: "acmebank.asia", industry_vertical: null, primary_jurisdiction: null,
  category_value: "Banking", category_confidence: 88, category_alternatives: ["Fintech"],
  region: ["APAC"],
  voice_samples: [{ src: "home", text: "Hi" }],
  products: [
    { name: "Save", category: "Deposit", url: null, confidence: 70 },
    { name: "Loan", category: "Credit", url: null, confidence: 60 },
    { name: "Card", category: "Credit", url: null, confidence: 50 },
  ],
  competitors: [{ name: "C1", domain: "c1.com", match_score: 42 }],
  media_matches: [],
  extraction_meta: null,
  created_at: "2026-05-18T00:00:00Z", updated_at: "2026-05-18T00:00:00Z",
} as unknown as BrandProfileResponse;

describe("toExtractedBrand", () => {
  it("snake to camel, null-coalesce, synth fields, productMoreCount", () => {
    const eb = toExtractedBrand(RESP);
    expect(eb.url).toBe("acmebank.asia");
    expect(eb.name).toBe("Acme Bank");
    expect(eb.legalName).toBe("");
    expect(eb.category).toEqual({ value: "Banking", confidence: 88, alternatives: ["Fintech"] });
    expect(eb.products).toHaveLength(3);
    expect(eb.products[0]).toMatchObject({ name: "Save", picked: true });
    expect(eb.products[0].id).toBeTruthy();
    expect(eb.products[0].icon).toBeTruthy();
    expect(eb.competitors[0].matchScore).toBe(42);
    expect(eb.productMoreCount).toBe(1);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && npx vitest run src/lib/onboarding/projection.test.ts`
Expected: FAIL — `./projection` missing.

- [ ] **Step 3: Write the projection** (write `slug`'s id as a template literal when implementing)

```ts
// web/src/lib/onboarding/projection.ts
import type { ExtractedBrand } from "@/components/onboarding-v2/data";
import type { BrandProfileResponse } from "@/lib/cortex-api";

export const VISIBLE_PRODUCTS = 2;

const s = (v: string | null | undefined): string => v ?? "";
const slug = (v: string, i: number): string =>
  v.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "") + "-" + i;

export function toExtractedBrand(p: BrandProfileResponse): ExtractedBrand {
  const products = (p.products ?? []).map((raw, i) => {
    const r = raw as { name: string; category: string; url: string | null; confidence: number };
    return {
      id: slug(r.name || "product", i),
      name: r.name,
      category: r.category,
      url: s(r.url),
      icon: "📦",
      picked: i < VISIBLE_PRODUCTS,
      confidence: r.confidence ?? 0,
    };
  });
  const competitors = (p.competitors ?? []).map((raw, i) => {
    const r = raw as { name: string; domain: string | null; match_score: number };
    return {
      id: slug(r.name || "competitor", i),
      name: r.name,
      domain: s(r.domain),
      picked: true,
      matchScore: r.match_score ?? 0,
    };
  });
  const voiceSamples = (p.voice_samples ?? []).map((raw) => {
    const r = raw as { src: string; text: string };
    return { src: r.src, text: r.text, picked: true };
  });
  return {
    url: s(p.source_url) || s(p.name),
    name: s(p.name),
    legalName: s(p.legal_name),
    tagline: s(p.tagline),
    monogram: s(p.monogram),
    brandColor: s(p.brand_color),
    category: {
      value: s(p.category_value),
      confidence: p.category_confidence ?? 0,
      alternatives: p.category_alternatives ?? [],
    },
    region: p.region ?? [],
    founded: s(p.founded),
    about: s(p.about),
    voiceSamples,
    products,
    productMoreCount: Math.max(0, products.length - VISIBLE_PRODUCTS),
    competitors,
  };
}
```

- [ ] **Step 4: Run projection test (PASS)**

Run: `cd web && npx vitest run src/lib/onboarding/projection.test.ts`
Expected: PASS (1 passed)

- [ ] **Step 5: Write the failing http-api test**

```ts
// web/src/lib/onboarding/http-api.test.ts
import { describe, expect, it, vi } from "vitest";

vi.mock("@/app/(auth)/onboarding/v2/analyze-actions", () => ({
  startAnalyzeAction: vi.fn(async () => ({ job_id: "j1", status: "pending" })),
  pollAnalyzeAction: vi
    .fn()
    .mockResolvedValueOnce({ job_id: "j1", status: "running" })
    .mockResolvedValueOnce({
      job_id: "j1",
      status: "succeeded",
      profile: {
        brand_id: "b1", name: "Acme", legal_name: null, tagline: null, monogram: null,
        brand_color: null, founded: null, about: null, source_url: "acme.test",
        industry_vertical: null, primary_jurisdiction: null, category_value: "Bank",
        category_confidence: 9, category_alternatives: [], region: [],
        voice_samples: [], products: [], competitors: [], media_matches: [],
        extraction_meta: null, created_at: "x", updated_at: "x",
      },
    }),
}));

import { HttpOnboardingApi } from "./http-api";

describe("HttpOnboardingApi", () => {
  it("analyzeBrand polls to success and projects", async () => {
    const api = new HttpOnboardingApi({ pollMs: 1, maxPolls: 10 });
    const eb = await api.analyzeBrand("acme.test");
    expect(eb.name).toBe("Acme");
    expect(eb.category.value).toBe("Bank");
  });

  it("analyzeBrand throws on failed job", async () => {
    const mod = await import("@/app/(auth)/onboarding/v2/analyze-actions");
    (mod.pollAnalyzeAction as unknown as { mockResolvedValue: (v: unknown) => void }).mockResolvedValue(
      { job_id: "j1", status: "failed", error: "boom" },
    );
    const api = new HttpOnboardingApi({ pollMs: 1, maxPolls: 5 });
    await expect(api.analyzeBrand("x")).rejects.toThrow();
  });

  it("non-analyze methods still return modeled data", async () => {
    const api = new HttpOnboardingApi();
    expect(await api.getCrawlTasks()).toBeInstanceOf(Array);
    expect(await api.getDeployLog()).toBeInstanceOf(Array);
  });
});
```

- [ ] **Step 6: Run test to verify it fails**

Run: `cd web && npx vitest run src/lib/onboarding/http-api.test.ts`
Expected: FAIL — `./http-api` missing.

- [ ] **Step 7: Write `HttpOnboardingApi`** (use a template literal for the error string when implementing)

```ts
// web/src/lib/onboarding/http-api.ts
import {
  pollAnalyzeAction,
  startAnalyzeAction,
} from "@/app/(auth)/onboarding/v2/analyze-actions";
import {
  CRAWL_TASKS,
  DEPLOY_AGENTS,
  DEPLOY_LOG,
  LIVE_QUESTIONS,
  MEDIA_NETWORK,
  VOICE_TONES,
  type CrawlTask,
  type DeployAgent,
  type DeployLogLine,
  type ExtractedBrand,
  type LiveQuestion,
  type Media,
  type VoiceTone,
} from "@/components/onboarding-v2/data";

import type { OnboardingApi } from "./api";
import { toExtractedBrand } from "./projection";

const sleep = (ms: number): Promise<void> =>
  new Promise((r) => setTimeout(r, ms));

export class HttpOnboardingApi implements OnboardingApi {
  private readonly pollMs: number;
  private readonly maxPolls: number;

  constructor(opts: { pollMs?: number; maxPolls?: number } = {}) {
    this.pollMs = opts.pollMs ?? 2000;
    this.maxPolls = opts.maxPolls ?? 90;
  }

  async analyzeBrand(url: string): Promise<ExtractedBrand> {
    const started = await startAnalyzeAction(url);
    let job = started;
    for (let i = 0; i < this.maxPolls; i++) {
      if (job.status === "succeeded") {
        if (!job.profile) throw new Error("analyze succeeded without a profile");
        return toExtractedBrand(job.profile);
      }
      if (job.status === "failed") {
        throw new Error("brand analysis failed: " + (job.error ?? "unknown"));
      }
      await sleep(this.pollMs);
      job = await pollAnalyzeAction(started.job_id);
    }
    throw new Error("brand analysis timed out");
  }

  // SP-3b / later: no backend yet — modeled data keeps the wizard whole.
  getCrawlTasks(): Promise<CrawlTask[]> {
    return Promise.resolve(CRAWL_TASKS);
  }
  getMediaNetwork(): Promise<Media[]> {
    return Promise.resolve(MEDIA_NETWORK);
  }
  getLiveQuestions(): Promise<LiveQuestion[]> {
    return Promise.resolve(LIVE_QUESTIONS);
  }
  getVoiceTones(): Promise<VoiceTone[]> {
    return Promise.resolve(VOICE_TONES);
  }
  getDeployAgents(): Promise<DeployAgent[]> {
    return Promise.resolve(DEPLOY_AGENTS);
  }
  getDeployLog(): Promise<DeployLogLine[]> {
    return Promise.resolve(DEPLOY_LOG);
  }
}
```

- [ ] **Step 8: Run test to verify it passes**

Run: `cd web && npx vitest run src/lib/onboarding/http-api.test.ts`
Expected: PASS (3 passed)

- [ ] **Step 9: Commit**

```bash
git add web/src/lib/onboarding/projection.ts web/src/lib/onboarding/projection.test.ts web/src/lib/onboarding/http-api.ts web/src/lib/onboarding/http-api.test.ts
git commit -m "feat(web): HttpOnboardingApi + BrandProfile->ExtractedBrand projection

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 14: Flip the seam (`getOnboardingApi()`), keep mock parity green

**Files:**
- Modify: `web/src/lib/onboarding/api.ts` (the `// SEAM:` line)
- Test: `web/src/lib/onboarding/get-onboarding-api.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// web/src/lib/onboarding/get-onboarding-api.test.ts
import { afterEach, describe, expect, it, vi } from "vitest";

import { getOnboardingApi } from "./api";
import { HttpOnboardingApi } from "./http-api";
import { MockOnboardingApi } from "./mock-api";

afterEach(() => vi.unstubAllEnvs());

describe("getOnboardingApi", () => {
  it("returns HttpOnboardingApi when the flag is set", () => {
    vi.stubEnv("NEXT_PUBLIC_CORTEX_ONBOARDING_HTTP", "1");
    expect(getOnboardingApi()).toBeInstanceOf(HttpOnboardingApi);
  });
  it("defaults to MockOnboardingApi", () => {
    vi.stubEnv("NEXT_PUBLIC_CORTEX_ONBOARDING_HTTP", "");
    expect(getOnboardingApi()).toBeInstanceOf(MockOnboardingApi);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && npx vitest run src/lib/onboarding/get-onboarding-api.test.ts`
Expected: FAIL — currently always returns `MockOnboardingApi`.

- [ ] **Step 3: Edit the seam in `web/src/lib/onboarding/api.ts`**

Add the import and replace the `getOnboardingApi` body:

```ts
import { HttpOnboardingApi } from "./http-api";
// ...
export function getOnboardingApi(): OnboardingApi {
  // SEAM (SP-3a): real adapter behind a flag; default stays mock.
  if (process.env.NEXT_PUBLIC_CORTEX_ONBOARDING_HTTP === "1") {
    return new HttpOnboardingApi();
  }
  return new MockOnboardingApi();
}
```

- [ ] **Step 4: Run the onboarding suite (all green incl. mock parity)**

Run: `cd web && npx vitest run src/lib/onboarding/`
Expected: PASS — `get-onboarding-api`, `mock-api.test.ts` (9 parity), `projection`, `http-api`.

- [ ] **Step 5: Commit**

```bash
git add web/src/lib/onboarding/api.ts web/src/lib/onboarding/get-onboarding-api.test.ts
git commit -m "feat(web): flag-gated HttpOnboardingApi seam (default stays mock)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 15: Full-suite green + lint/type gates (both packages)

**Files:** none (verification + fixups only)

- [ ] **Step 1: api gates (CI-verbatim, cache cleaned)**

Run, from `api/` (DB up via `docker-compose up -d`):
```
cd api
uv run ruff clean
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src
uv run pytest
```
Expected: ruff clean, format clean, mypy `Success`, pytest all pass (incl. `-m integration`). Fix any failure only in the owning task's files; re-run.

- [ ] **Step 2: web gates**

Run:
```
cd web
npm run lint
npm run type-check
npm test
```
Expected: eslint clean, tsc clean, vitest all pass (pre-existing mock-parity 9 + the new SP-3a suites).

- [ ] **Step 3: Migration round-trip (final)**

Run, from `api/`:
```
uv run alembic upgrade head
uv run alembic downgrade base
uv run alembic upgrade head
```
Expected: all succeed (confirms the ENUM drop in `downgrade()`).

- [ ] **Step 4: Commit any fixups**

```bash
git add -A
git commit -m "chore(sp3a): lint/type/test green across api + web

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

(If nothing changed, skip.)

---

## Notes for the executor

- **Confirm fixture names first.** Tasks 4/7/9 reuse the existing integration harness in `api/tests/integration/test_brand_profile_repo.py` and `test_brand_profile_api.py` (transactional Postgres fixture + DI/auth overrides). Open those files; match the exact fixture/cm names (`db_session` / `database_client` / the client context manager). The names in this plan's test code stand in for *that* harness's real names.
- **No `mock.patch`.** SP-2 is injected via `AnalyzeJobService(..., _extract=<fake>)`; the DI provider is overridden via `BrandContainer.<provider>.override(...)`. House convention.
- **Capability gates:** `EDIT_BRAND_SETTINGS` (POST) / `VIEW_BRAND_DASHBOARD` (GET). Both exist; do not add a new capability.
- **Error mapping:** SP-2 `cortex_brand_extract.errors.{UpstreamTimeoutError,UpstreamError,ExtractError}` → cortex `core.exceptions.{UpstreamTimeoutError,UpstreamError}` chained `from e` (→ 504/502). Job is marked `failed` regardless.
- **TS template literals:** code blocks use string concatenation only to satisfy the docs-write security check; implement with template literals (house eslint `prefer-template`). Identical behaviour.
- **Out of scope** (do not build): SP-3b public surface, real backends for the 6 modeled methods, Redis worker, job-history UI, the deferred #28-Issue-1 / #31-Issue-3 follow-ups.
