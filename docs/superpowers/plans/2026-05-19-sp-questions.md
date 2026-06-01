# SP-QUESTIONS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Onboarding step 4 "Weekly questions" shows the **real AIGC Q&A units readers engaged with across the Mlytics network this week**, LLM-ranked/framed for the brand, persisted and deterministic per brand — EN and 繁中.

**Architecture:** Approach A — `service/questions/` is a 1:1 clone of the merged `service/media_network/` (the canonical pattern; spec D9). A periodic Databricks snapshot of real `question_title`/`question_clicks`/`publisher_name`/`event_date` from `aigc_prod.aigc_metrics.aigc_clickstream_metrics` lands in cortex; an SP-3a-style async job runs an LLM matcher (output strictly ⊆ snapshot; `competitorMentions` ⊆ the brand's real `brand_profile.competitors`; `intent`/`score` LLM-derived) and persists per brand. Web ADDs a `getLiveQuestions()` seam fetched **post-analyze** (d8345ff-correct) in both EN + 繁中 wizards.

**Tech Stack:** FastAPI · Python 3.12 (uv) · SQLModel + Alembic (asyncpg) · dependency_injector · structlog · pydantic v2 · databricks-sql-connector (wrapped) · `cortex_brand_extract` Claude provider · Next.js 16 (Server Actions) · vitest. ruff+mypy strict, pytest.

**Spec:** `docs/superpowers/specs/2026-05-19-sp-questions-design.md`. **Worktree:** `cortex-wt/sp-questions`, branch `feat/sp-questions` (off `develop` @ `14069ad`, SP-MEDIA #36 merged). **Canonical mirror:** the merged `service/media_network/` + `app/api/media_network/` + `scripts/sync_media_network.py` + the d8345ff web wiring + `orchestrator-media-callsite.test.ts` + plan `docs/superpowers/plans/2026-05-19-sp-media.md`. `@owl review` for re-review (`@owl verify` is infra-broken). Run `api/` cmds from `cortex-wt/sp-questions/api` with `uv`; `web/` from `.../web`.

---

## File Structure

**Create (api):** `service/questions/__init__.py`, `config.py`, `model/__init__.py`, `model/job.py` (`BrandWeeklyQuestions`+`QuestionJobStatus`), `model/question.py` (`WeeklyQuestion`), `repo/__init__.py`, `repo/question_repo.py` (snapshot upsert/list), `repo/brand_questions_repo.py` (per-brand CRUD/dedupe/sweep), `matcher.py`, `job_service.py` (`QuestionsJobService`), `snapshot_sync.py`, `container.py`; `app/api/questions/__init__.py`, `dto.py`, `router.py`; `api/scripts/sync_weekly_questions.py`. **Modify (api):** `alembic/env.py` (+2 imports), `alembic/versions/f6a7b8c9d0e1_weekly_questions.py` (new), `main.py` (wire container+router+lifespan).

**Create/Modify (web):** modify `src/lib/onboarding/api.ts` (+`getLiveQuestions` on interface & both adapters), `src/lib/onboarding/mock-api.ts` (return `LIVE_QUESTIONS`), `src/lib/onboarding/http-api.ts` (real), `src/lib/cortex-api.ts` (+start/poll+`WeeklyQuestionsDTO`), `src/lib/onboarding/projection.ts` (+`projectWeeklyQuestions`, `import type` DTO), create `src/app/(auth)/onboarding/v2/weekly-questions-actions.ts`, modify `src/app/(auth)/onboarding/v2/page.tsx` + `.../zh-TW/page.tsx` (post-analyze fetch + prop), `src/components/onboarding-v2/step-questions.tsx` + `onboarding-v2-zh/step-questions.tsx` (prop-driven).

**Tests:** `api/tests/unit/test_questions_config.py`, `test_questions_models.py`, `test_questions_matcher.py`, `test_questions_snapshot_sync.py`, `test_questions_container.py`; `api/tests/integration/test_questions_repos.py`, `test_questions_job.py`, `test_questions_api.py`; `web/src/lib/onboarding/projection.test.ts` (extend); `web/src/components/onboarding-v2/__tests__/step-questions-real.test.tsx`; `web/src/app/(auth)/onboarding/v2/__tests__/orchestrator-questions-callsite.test.ts`.

`LiveQuestion` shape (existing, `web/src/components/onboarding-v2/data.ts`): `{ id, text, media, intent: "Explore"|"Understand"|"Evaluate"|"Act", score, asks, when, competitorMentions: string[] }`.

---

## Task 1: Package skeleton + config

**Files:** Create `service/questions/{__init__,config}.py`, `service/questions/model/__init__.py`, `service/questions/repo/__init__.py`, `app/api/questions/__init__.py`; Test `api/tests/unit/test_questions_config.py`.

- [ ] **Step 1: Failing test**
```python
# api/tests/unit/test_questions_config.py
from cortex_api.service.questions.config import Config


def test_defaults():
    c = Config()
    assert c.question_count == 6
    assert c.stale_job_seconds == 180
    assert c.dbx_catalog == "aigc_prod"
```
- [ ] **Step 2:** `cd api && uv run pytest tests/unit/test_questions_config.py -q` → FAIL (ModuleNotFoundError).
- [ ] **Step 3:** Create the 4 empty `__init__.py` (0 bytes). Create `service/questions/config.py` (mirror `service/media_network/config.py`; `question_count` replaces `outlet_count`):
```python
# api/src/cortex_api/service/questions/config.py
"""Questions domain config."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Weekly-questions service config."""

    model_config = SettingsConfigDict(env_prefix="CORTEX_QUESTIONS_", extra="forbid")

    question_count: int = 6
    stale_job_seconds: int = 180
    dbx_catalog: str = "aigc_prod"
```
(Verify against `service/media_network/config.py` — match its exact import/`SettingsConfigDict` style; only the env_prefix + first field name/value differ.)
- [ ] **Step 4:** Run test → PASS.
- [ ] **Step 5:** Commit
```bash
git add api/src/cortex_api/service/questions api/src/cortex_api/app/api/questions api/tests/unit/test_questions_config.py
git commit -m "feat(sp-questions): questions package skeleton + config"
```

---

## Task 2: SQLModel tables — `WeeklyQuestion` + `BrandWeeklyQuestions`

**Files:** Create `service/questions/model/question.py`, `model/job.py`; Test `api/tests/unit/test_questions_models.py`.

- [ ] **Step 1: Failing test**
```python
# api/tests/unit/test_questions_models.py
import uuid

from cortex_api.service.questions.model.job import BrandWeeklyQuestions, QuestionJobStatus
from cortex_api.service.questions.model.question import WeeklyQuestion


def test_question_table():
    q = WeeklyQuestion(id="h1", question_title="三大法人賣超?", publisher_name="Cmnews", clicks=93)
    assert q.id == "h1"
    assert q.clicks == 93


def test_job_defaults():
    j = BrandWeeklyQuestions(brand_id=uuid.uuid4())
    assert j.status == QuestionJobStatus.PENDING
    assert j.questions == []
```
- [ ] **Step 2:** `cd api && uv run pytest tests/unit/test_questions_models.py -q` → FAIL.
- [ ] **Step 3:** Read `service/media_network/model/member.py` + `model/job.py` and mirror them. Create `model/question.py`:
```python
# api/src/cortex_api/service/questions/model/question.py
from __future__ import annotations

from datetime import date, datetime

from sqlmodel import Field, SQLModel


class WeeklyQuestion(SQLModel, table=True):
    """Snapshot of one real AIGC Q&A unit readers engaged with (from Databricks)."""

    __tablename__ = "weekly_question"

    id: str = Field(primary_key=True, max_length=64)  # hash(question_title|publisher_name)
    question_title: str = Field(max_length=2048)
    publisher_name: str = Field(max_length=255)
    clicks: int = Field(default=0)
    last_event_date: date | None = Field(default=None)
    synced_at: datetime = Field(default_factory=datetime.utcnow)
```
- [ ] **Step 4:** Create `model/job.py` (mirror `media_network/model/job.py` exactly — same `sa_column` named-enum pattern, JSONB list helper, FK, timestamp `server_default`/`onupdate`; rename `mediajobstatus`→`questionjobstatus`, `outlets`→`questions`):
```python
# api/src/cortex_api/service/questions/model/job.py
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class QuestionJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


def _jsonb_list() -> Any:
    return Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))


class BrandWeeklyQuestions(SQLModel, table=True):
    """The persisted, deterministic weekly-questions result for one brand."""

    __tablename__ = "brand_weekly_questions"

    brand_id: UUID = Field(foreign_key="brand.id", primary_key=True)
    status: QuestionJobStatus = Field(
        default=QuestionJobStatus.PENDING,
        sa_column=Column(
            SAEnum(QuestionJobStatus, name="questionjobstatus",
                   values_callable=lambda e: [m.value for m in e]),
            nullable=False,
        ),
    )
    error: str | None = Field(default=None)
    questions: list[dict[str, Any]] = Field(default_factory=list, sa_column=_jsonb_list())
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow}
    )
```
**RECONCILE:** open `service/media_network/model/job.py` and make this byte-for-byte structurally identical (same imports, same `SAEnum`/`values_callable`, same `_jsonb_list`, same FK + timestamp declarations) — only `QuestionJobStatus`/`questionjobstatus`/`BrandWeeklyQuestions`/`brand_weekly_questions`/`questions` differ. If the sibling differs, follow the sibling.
- [ ] **Step 5:** Run test → 2 passed; `uv run python -c "import cortex_api.service.questions.model.question, cortex_api.service.questions.model.job"`.
- [ ] **Step 6:** Commit
```bash
git add api/src/cortex_api/service/questions/model api/tests/unit/test_questions_models.py
git commit -m "feat(sp-questions): WeeklyQuestion + BrandWeeklyQuestions models"
```

---

## Task 3: Alembic migration

**Files:** Modify `api/alembic/env.py`; Create `api/alembic/versions/f6a7b8c9d0e1_weekly_questions.py`.

- [ ] **Step 1:** Verify head: `cd api && docker-compose up -d && sleep 3 && uv run alembic heads` → expect `e5f6a7b8c9d0`. If different, use the real single head as `down_revision` and report.
- [ ] **Step 2:** Add to `alembic/env.py` after the media_network model imports (same `# noqa: F401` style):
```python
from cortex_api.service.questions.model.question import WeeklyQuestion  # noqa: F401
from cortex_api.service.questions.model.job import BrandWeeklyQuestions  # noqa: F401
```
- [ ] **Step 3:** Create `api/alembic/versions/f6a7b8c9d0e1_weekly_questions.py` — base on `e5f6a7b8c9d0_media_network.py` (read it; mirror its column-type idioms — `sqlmodel.sql.sqltypes.AutoString`, enum decl, JSONB server_default, `server_default=sa.func.now()` + `onupdate`, explicit enum drop):
```python
from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f6a7b8c9d0e1"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "weekly_question",
        sa.Column("id", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column("question_title", sqlmodel.sql.sqltypes.AutoString(length=2048), nullable=False),
        sa.Column("publisher_name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("clicks", sa.Integer(), nullable=False),
        sa.Column("last_event_date", sa.Date(), nullable=True),
        sa.Column("synced_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "brand_weekly_questions",
        sa.Column("brand_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.Enum("pending", "running", "succeeded", "failed", name="questionjobstatus"), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("questions", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(["brand_id"], ["brand.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("brand_id"),
    )


def downgrade() -> None:
    op.drop_table("brand_weekly_questions")
    op.drop_table("weekly_question")
    sa.Enum(name="questionjobstatus").drop(op.get_bind(), checkfirst=True)
```
(Reconcile column SA types to whatever `e5f6a7b8c9d0_media_network.py` uses for equivalent fields so autogenerate drift is empty.)
- [ ] **Step 4:** `uv run alembic upgrade head` → head `f6a7b8c9d0e1`.
- [ ] **Step 5:** Drift check: `uv run alembic revision --autogenerate -m "TEMP drift"` — its `upgrade()`/`downgrade()` must contain NO ops referencing `weekly_question`/`brand_weekly_questions`/`questionjobstatus` (pre-existing unrelated drift OK). `rm` the TEMP file (do not commit it).
- [ ] **Step 6:** Round-trip: `uv run alembic downgrade e5f6a7b8c9d0 && uv run alembic upgrade head` — both succeed (no `type "questionjobstatus" already exists`). `uv run alembic current` → `f6a7b8c9d0e1`.
- [ ] **Step 7:** Commit
```bash
git add api/alembic/env.py api/alembic/versions/f6a7b8c9d0e1_weekly_questions.py
git commit -m "feat(sp-questions): migration — weekly_question + brand_weekly_questions"
```

---

## Task 4: Repos — `QuestionRepo` + `BrandQuestionsRepo`

**Files:** Create `service/questions/repo/question_repo.py`, `repo/brand_questions_repo.py`; Test `api/tests/integration/test_questions_repos.py`.

- [ ] **Step 1: Failing integration test** (mirror `tests/integration/test_media_repos.py`):
```python
# api/tests/integration/test_questions_repos.py
import uuid

import pytest
import sqlalchemy as sa

from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.questions.model.job import BrandWeeklyQuestions, QuestionJobStatus
from cortex_api.service.questions.model.question import WeeklyQuestion
from cortex_api.service.questions.repo.brand_questions_repo import BrandQuestionsRepo
from cortex_api.service.questions.repo.question_repo import QuestionRepo

pytestmark = pytest.mark.integration


@pytest.fixture()
def db():
    return InfraContainer()._database_client_factory()


async def test_question_upsert_idempotent(db):
    repo = QuestionRepo()
    async with db.session() as s:
        await repo.upsert_all(s, [WeeklyQuestion(id="x1", question_title="Q?", publisher_name="P", clicks=10)])
    async with db.session() as s:
        await repo.upsert_all(s, [WeeklyQuestion(id="x1", question_title="Q?", publisher_name="P", clicks=20)])
    async with db.session() as s:
        rows = await repo.list_all(s)
    assert [(r.id, r.clicks) for r in rows if r.id == "x1"] == [("x1", 20)]


async def test_brand_questions_in_flight_and_persist(db):
    repo = BrandQuestionsRepo()
    bid = uuid.uuid4()
    async with db.session() as s:
        await s.execute(sa.text("insert into brand (id, display_name) values (:i,'T') on conflict do nothing"), {"i": str(bid)})
        await repo.create(s, BrandWeeklyQuestions(brand_id=bid))
    async with db.session() as s:
        assert (await repo.get(s, bid)) is not None
        assert (await repo.find_in_flight(s, bid)) is not None
    async with db.session() as s:
        await repo.mark_succeeded(s, bid, [{"id": "x1"}])
    async with db.session() as s:
        done = await repo.get(s, bid)
    assert done.status == QuestionJobStatus.SUCCEEDED and done.questions == [{"id": "x1"}]


async def test_brand_questions_create_resets_stale_row(db):
    repo = BrandQuestionsRepo()
    bid = uuid.uuid4()
    async with db.session() as s:
        await s.execute(sa.text("insert into brand (id, display_name) values (:i,'R') on conflict do nothing"), {"i": str(bid)})
        await repo.create(s, BrandWeeklyQuestions(brand_id=bid))
    async with db.session() as s:
        await repo.mark_succeeded(s, bid, [{"id": "x1"}])
    async with db.session() as s:
        await repo.create(s, BrandWeeklyQuestions(brand_id=bid))
    async with db.session() as s:
        row = await repo.get(s, bid)
    assert row.status == QuestionJobStatus.PENDING
    assert row.error is None
    assert row.questions == []   # list, not the string "[]"
```
- [ ] **Step 2:** `cd api && uv run pytest tests/integration/test_questions_repos.py -q -m integration` → FAIL.
- [ ] **Step 3:** Create `repo/question_repo.py` by mirroring `service/media_network/repo/member_repo.py` (PG `on_conflict_do_update`, same session/exec idioms): `list_all(session)` and `upsert_all(session, questions)`; `_REPLACE = ("question_title","publisher_name","clicks","last_event_date","synced_at")`; conflict target `["id"]`. Read the sibling and replicate exactly (only model/columns differ).
- [ ] **Step 4:** Create `repo/brand_questions_repo.py` mirroring `service/media_network/repo/brand_media_repo.py` EXACTLY — `get`, `find_in_flight` (PENDING/RUNNING), `create` (insert-or-reset; **the `on_conflict_do_update` `questions` reset MUST be a Python list `[]`, NOT the string `"[]"`** — this is the SP-MEDIA @owl bug `e91ac41`; replicate the fixed version), `mark_running`/`mark_succeeded`/`mark_failed`, `sweep_stale`. Replicate the sibling's session/flush mechanics.
- [ ] **Step 5:** `cd api && uv run pytest tests/integration/test_questions_repos.py -q -m integration` → 3 passed. `uv run ruff check src/cortex_api/service/questions/repo && uv run mypy src/cortex_api/service/questions/repo` clean.
- [ ] **Step 6:** Commit
```bash
git add api/src/cortex_api/service/questions/repo api/tests/integration/test_questions_repos.py
git commit -m "feat(sp-questions): question + brand-questions repos"
```

---

## Task 5: LLM matcher (⊆-snapshot + competitorMentions⊆real + intent/score)

**Files:** Create `service/questions/matcher.py`; Test `api/tests/unit/test_questions_matcher.py`.

- [ ] **Step 1: Failing test** (mirror `test_media_matcher.py`; FakeProvider returns `LLMResult(data=...)`):
```python
# api/tests/unit/test_questions_matcher.py
from cortex_api.service.questions.matcher import match_questions
from cortex_api.service.questions.model.question import WeeklyQuestion


class FakeProvider:
    model = "fake"
    def __init__(self, payload): self._payload = payload
    async def complete_json(self, *, system, user, schema):
        from cortex_brand_extract.llm.base import LLMResult
        return LLMResult(data=self._payload)


SNAP = [
    WeeklyQuestion(id="a", question_title="Best ETF for dividends?", publisher_name="CMoney", clicks=300),
    WeeklyQuestion(id="b", question_title="How to open USD account?", publisher_name="NOWnews", clicks=100),
]
PROFILE = {"name": "Acme Bank", "category": "Banking", "competitors": ["Cathay", "CTBC"], "products": [], "about": ""}


async def test_subset_enforced_and_competitor_subset():
    prov = FakeProvider({"questions": [
        {"id": "a", "intent": "Evaluate", "score": 90, "competitorMentions": ["Cathay", "FAKECORP"]},
        {"id": "ZZZ", "intent": "Act", "score": 80, "competitorMentions": []},
    ]})
    out = await match_questions(PROFILE, SNAP, prov, question_count=6)
    ids = [q["id"] for q in out]
    assert "ZZZ" not in ids and set(ids).issubset({"a", "b"})
    a = next(q for q in out if q["id"] == "a")
    assert a["text"] == "Best ETF for dividends?" and a["media"] == "CMoney" and a["asks"] == 300
    assert a["intent"] in ("Explore", "Understand", "Evaluate", "Act")
    assert set(a["competitorMentions"]).issubset({"Cathay", "CTBC"})  # FAKECORP dropped


async def test_deterministic_backfill_when_empty():
    out = await match_questions(PROFILE, SNAP, FakeProvider({"questions": []}), question_count=6)
    assert [q["id"] for q in out] == ["a", "b"]      # clicks desc
    assert all(q["text"] and q["intent"] for q in out)


async def test_malformed_payload_never_raises():
    for bad in ({"questions": {"x": 1}}, {"questions": 42}, {"questions": [{"id": "a", "score": "NaN"}]}):
        out = await match_questions(PROFILE, SNAP, FakeProvider(bad), question_count=6)
        assert set(q["id"] for q in out).issubset({"a", "b"})


async def test_truncated_to_count():
    prov = FakeProvider({"questions": [{"id": "a", "intent": "Act", "score": 50, "competitorMentions": []},
                                       {"id": "b", "intent": "Act", "score": 40, "competitorMentions": []}]})
    out = await match_questions(PROFILE, SNAP, prov, question_count=1)
    assert len(out) == 1
```
- [ ] **Step 2:** `cd api && uv run pytest tests/unit/test_questions_matcher.py -q` → FAIL.
- [ ] **Step 3:** Read `service/media_network/matcher.py`; create `service/questions/matcher.py` mirroring it (by-id index instead of by-host; `_fallback`; outer `try/except Exception  # noqa: BLE001`; `isinstance(raw, list)` guard; per-item `except (TypeError, ValueError, AttributeError): continue`):
```python
# api/src/cortex_api/service/questions/matcher.py
from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from cortex_brand_extract.llm.base import LLMProvider

from cortex_api.service.questions.model.question import WeeklyQuestion

_INTENTS = ("Explore", "Understand", "Evaluate", "Act")
_SYSTEM = (
    "You rank a fixed list of REAL reader questions for a brand. "
    "Only use question ids from the provided list — never invent questions. "
    "For each, classify intent as one of Explore|Understand|Evaluate|Act, give "
    "score 0-100 (relevance to the brand), and competitorMentions strictly chosen "
    "from the brand's competitor list (never invent competitors). "
    'Return JSON {"questions":[{id, intent, score, competitorMentions[]}]} best-first.'
)
_SCHEMA = {
    "type": "object",
    "properties": {"questions": {"type": "array", "items": {"type": "object",
        "properties": {"id": {"type": "string"}, "intent": {"type": "string"},
                       "score": {"type": "integer"},
                       "competitorMentions": {"type": "array", "items": {"type": "string"}}},
        "required": ["id", "intent", "score", "competitorMentions"]}}},
    "required": ["questions"],
}


def _when(q: WeeklyQuestion) -> str:
    return "" if q.last_event_date is None else q.last_event_date.isoformat()


def _base(q: WeeklyQuestion) -> dict[str, Any]:
    return {"id": q.id, "text": q.question_title, "media": q.publisher_name,
            "asks": q.clicks, "when": _when(q)}


def _fallback(q: WeeklyQuestion) -> dict[str, Any]:
    return {**_base(q), "intent": "Understand", "score": 50, "competitorMentions": []}


async def match_questions(
    profile: dict[str, Any],
    snapshot: Sequence[WeeklyQuestion],
    provider: LLMProvider,
    question_count: int,
) -> list[dict[str, Any]]:
    """Rank/frame REAL snapshot questions for the brand. Output ⊆ snapshot."""
    by_id = {q.id: q for q in snapshot}
    competitors = {str(c) for c in (profile.get("competitors") or [])}
    user = json.dumps({"brand": profile, "questions": [
        {"id": q.id, "text": q.question_title, "media": q.publisher_name, "clicks": q.clicks}
        for q in snapshot]}, ensure_ascii=False)
    try:
        result = await provider.complete_json(system=_SYSTEM, user=user, schema=_SCHEMA)
        raw = result.data.get("questions", [])
        if not isinstance(raw, list):
            raw = []
    except Exception:  # noqa: BLE001 — degrade to deterministic fallback, never fail closed
        raw = []

    picked: list[dict[str, Any]] = []
    seen: set[str] = set()
    for o in raw:
        try:
            if not isinstance(o, dict):
                continue
            qid = o.get("id")
            if qid not in by_id or qid in seen:
                continue
            q = by_id[qid]
            intent = str(o.get("intent", "Understand"))
            picked.append({
                **_base(q),
                "intent": intent if intent in _INTENTS else "Understand",
                "score": int(o.get("score", 0)),
                "competitorMentions": [c for c in (o.get("competitorMentions") or [])
                                       if str(c) in competitors],
            })
            seen.add(qid)
        except (TypeError, ValueError, AttributeError):
            continue

    if len(picked) < question_count:
        for q in sorted((q for q in snapshot if q.id not in seen),
                        key=lambda q: -(q.clicks or 0)):
            picked.append(_fallback(q))

    return picked[:question_count]
```
**RECONCILE** structure to `media_network/matcher.py` (same guard placement, same `# noqa`). If `cortex_brand_extract.llm.base` exposes a different `LLMProvider`/`LLMResult`/`complete_json` shape than the media matcher uses, match the REAL shape (read it).
- [ ] **Step 4:** Run → 4 passed; `uv run ruff check src/cortex_api/service/questions/matcher.py && uv run mypy src/cortex_api/service/questions/matcher.py` clean.
- [ ] **Step 5:** Commit
```bash
git add api/src/cortex_api/service/questions/matcher.py api/tests/unit/test_questions_matcher.py
git commit -m "feat(sp-questions): LLM matcher — ranks real questions, ⊆ snapshot, competitorMentions ⊆ real"
```

---

## Task 6: Snapshot sync (Databricks → `weekly_question`)

**Files:** Create `service/questions/snapshot_sync.py`; Test `api/tests/unit/test_questions_snapshot_sync.py`.

- [ ] **Step 1: Failing test** (mirror `test_media_snapshot_sync.py`; fakes; assert id=hash, mapping, failure-isolation, invalid-catalog raises):
```python
# api/tests/unit/test_questions_snapshot_sync.py
import contextlib
import pytest

from cortex_api.core.exceptions import BadRequestError, UpstreamError
from cortex_api.service.questions.snapshot_sync import sync_snapshot


class FakeDbx:
    def __init__(self, rows): self._rows = rows
    async def fetch_all(self, sql, params=None):
        if isinstance(self._rows, Exception):
            raise self._rows
        return self._rows


class FakeRepo:
    def __init__(self): self.upserted = None
    async def upsert_all(self, session, items): self.upserted = list(items)


class FakeDB:
    def session(self):
        @contextlib.asynccontextmanager
        async def _s():
            yield object()
        return _s()


async def test_maps_rows():
    dbx = FakeDbx([["Best ETF?", "CMoney", 300, "2026-05-15"]])
    repo = FakeRepo()
    n = await sync_snapshot(dbx, FakeDB(), repo, catalog_catalog="aigc_prod")
    assert n == 1
    q = repo.upserted[0]
    assert q.question_title == "Best ETF?" and q.publisher_name == "CMoney" and q.clicks == 300
    assert q.id and len(q.id) <= 64


async def test_query_failure_does_not_upsert():
    repo = FakeRepo()
    with pytest.raises(UpstreamError):
        await sync_snapshot(FakeDbx(UpstreamError("dbx down")), FakeDB(), repo, catalog_catalog="aigc_prod")
    assert repo.upserted is None


async def test_invalid_catalog_raises_before_fetch():
    repo = FakeRepo()
    with pytest.raises(BadRequestError):
        await sync_snapshot(FakeDbx([]), FakeDB(), repo, catalog_catalog="a; drop")
    assert repo.upserted is None
```
- [ ] **Step 2:** `cd api && uv run pytest tests/unit/test_questions_snapshot_sync.py -q` → FAIL.
- [ ] **Step 3:** Read `service/media_network/snapshot_sync.py`; create `service/questions/snapshot_sync.py` mirroring it (reuse the `_IDENTIFIER_RE` guard + `BadRequestError`; one `fetch_all` with the questions SQL; id = sha256(title|publisher) hex truncated 64):
```python
# api/src/cortex_api/service/questions/snapshot_sync.py
from __future__ import annotations

import hashlib
import re

import structlog

from cortex_api.core.exceptions import BadRequestError
from cortex_api.infra.database_client import DatabaseClient
from cortex_api.infra.databricks_client import DatabricksClient
from cortex_api.service.questions.model.question import WeeklyQuestion
from cortex_api.service.questions.repo.question_repo import QuestionRepo

_logger = structlog.get_logger(__name__)
_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _qid(title: str, publisher: str) -> str:
    return hashlib.sha256(f"{title}|{publisher}".encode()).hexdigest()[:64]


async def sync_snapshot(
    dbx: DatabricksClient,
    db: DatabaseClient,
    questions: QuestionRepo,
    catalog_catalog: str,
) -> int:
    """Pull the real weekly reader-question engagement and upsert the snapshot.

    Raises on Databricks failure WITHOUT upserting (prior snapshot intact).
    """
    if not _IDENTIFIER_RE.fullmatch(catalog_catalog):
        raise BadRequestError(f"dbx_catalog {catalog_catalog!r} is not a valid SQL identifier")
    rows = await dbx.fetch_all(
        f"select question_title, publisher_name, measure(question_clicks) as clicks, "
        f"max(event_date) as last_event_date "
        f"from {catalog_catalog}.aigc_metrics.aigc_clickstream_metrics "
        f"where event_date >= dateadd(day,-7,"
        f"(select max(event_date) from {catalog_catalog}.aigc_metrics.aigc_clickstream_metrics)) "
        f"and question_title is not null and question_title <> '' "
        f"group by question_title, publisher_name order by clicks desc"
    )
    items: list[WeeklyQuestion] = []
    for r in rows:
        title, pub = str(r[0]), str(r[1])
        items.append(WeeklyQuestion(
            id=_qid(title, pub), question_title=title[:2048], publisher_name=pub[:255],
            clicks=int(r[2]) if r[2] is not None else 0,
            last_event_date=r[3] if len(r) > 3 else None,
        ))
    if items:
        async with db.session() as session:
            await questions.upsert_all(session, items)
    _logger.info("weekly_questions_synced", questions=len(items))
    return len(items)
```
**RECONCILE:** match `media_network/snapshot_sync.py`'s exact `_IDENTIFIER_RE`/`BadRequestError` usage, `DatabaseClient`/`DatabricksClient` import paths, and `fetch_all` signature. If `last_event_date` arrives as a string from the connector, parse to `date` (mirror how media handles `wau`/types).
- [ ] **Step 4:** Run → 3 passed; ruff+mypy clean on the file.
- [ ] **Step 5:** Commit
```bash
git add api/src/cortex_api/service/questions/snapshot_sync.py api/tests/unit/test_questions_snapshot_sync.py
git commit -m "feat(sp-questions): Databricks->cortex weekly-question snapshot sync"
```

---

## Task 7: `QuestionsJobService`

**Files:** Create `service/questions/job_service.py`; Test `api/tests/integration/test_questions_job.py`.

- [ ] **Step 1: Failing test** (mirror `tests/integration/test_media_network_job.py`; seed brand + brand_profile via the same mechanism that test uses; fake `_match`):
```python
# api/tests/integration/test_questions_job.py
import uuid

import pytest
import sqlalchemy as sa

from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.questions.config import Config
from cortex_api.service.questions.job_service import QuestionsJobService
from cortex_api.service.questions.model.job import QuestionJobStatus
from cortex_api.service.questions.model.question import WeeklyQuestion
from cortex_api.service.questions.repo.brand_questions_repo import BrandQuestionsRepo
from cortex_api.service.questions.repo.question_repo import QuestionRepo

pytestmark = pytest.mark.integration


async def test_job_succeeds_and_persists():
    db = InfraContainer()._database_client_factory()
    bid = uuid.uuid4()
    async with db.session() as s:
        await s.execute(sa.text("insert into brand (id, display_name) values (:i,'T') on conflict do nothing"), {"i": str(bid)})
        await s.execute(sa.text("insert into brand_profile (brand_id, name) values (:i,'T') on conflict do nothing"), {"i": str(bid)})
        await QuestionRepo().upsert_all(s, [WeeklyQuestion(id="a", question_title="Q?", publisher_name="P", clicks=5)])

    async def fake_match(profile, snapshot, provider, question_count):
        return [{"id": "a", "text": "Q?", "media": "P", "asks": 5, "when": "",
                 "intent": "Act", "score": 99, "competitorMentions": []}]

    svc = QuestionsJobService(db, BrandQuestionsRepo(), QuestionRepo(), Config(),
                              BrandProfileRepo(), provider=object(), _match=fake_match)
    await svc.start(bid)
    await svc.drain()
    done = await svc.get(bid)
    assert done.status == QuestionJobStatus.SUCCEEDED
    assert done.questions[0]["id"] == "a"
    again = await svc.start(bid)
    assert again.status == QuestionJobStatus.SUCCEEDED
```
- [ ] **Step 2:** `cd api && docker-compose up -d && uv run alembic upgrade head && uv run pytest tests/integration/test_questions_job.py -q -m integration` → FAIL.
- [ ] **Step 3:** Read `service/media_network/job_service.py` IN FULL; create `service/questions/job_service.py` as a structural mirror. **Constructor signature exactly:** `__init__(self, database_client, brand_questions_repo, question_repo, config, brand_profile_repo: BrandProfileRepo, provider=None, _match=match_questions)` — store as `self._db,self._jobs,self._snap,self._config,self._brand_profile_repo,self._provider,self._match`, `self._tasks: dict[asyncio.Task[None], UUID] = {}`. `start(brand_id, regenerate=False)` dedupe + `asyncio.create_task(self._run(brand_id))` + `add_done_callback`. `get` raises the same not-found exception the sibling uses. `sweep_stale`, `drain`, `cancel_all` mirror the sibling. `_run`: mark_running → `profile = await self._brand_profile_repo.get(session, brand_id)` (NOT raw SQL) mapped to a dict (`name`,`category`(from the real industry/vertical field),`competitors`,`products`,`about` — use the SAME field mapping `media_network/job_service.py` uses) → `snapshot = await self._snap.list_all(session)` → `await self._match(profile, snapshot, self._provider, self._config.question_count)` → `mark_succeeded`; `except asyncio.CancelledError: raise` before `except Exception` → `mark_failed`. Copy the sibling's exact profile-dict construction.
- [ ] **Step 4:** Run → passed; ruff+mypy clean on the file.
- [ ] **Step 5:** Commit
```bash
git add api/src/cortex_api/service/questions/job_service.py api/tests/integration/test_questions_job.py
git commit -m "feat(sp-questions): QuestionsJobService (async job, dedupe, sweep)"
```

---

## Task 8: DI container

**Files:** Create `service/questions/container.py`; Test `api/tests/unit/test_questions_container.py`.

- [ ] **Step 1: Failing test**
```python
# api/tests/unit/test_questions_container.py
from cortex_api.service.questions.container import Container


def test_container_provides_service_and_sync():
    c = Container()
    assert c.job_service() is not None
    assert callable(c.run_snapshot_sync)
```
- [ ] **Step 2:** `cd api && uv run pytest tests/unit/test_questions_container.py -q` → FAIL.
- [ ] **Step 3:** Read `service/media_network/container.py`; create `service/questions/container.py` mirroring it 1:1 (same `providers.Container(InfraContainer)`, `database_client`/`databricks_client` from infra factories, `Config` singleton, `QuestionRepo`/`BrandQuestionsRepo`/`BrandProfileRepo` singletons, `analyze_config = Singleton(AnalyzeConfig)`, `provider = Singleton(build_provider, analyze_config)`, `job_service = Singleton(QuestionsJobService, …)` with the Task-7 kwargs, `run_snapshot_sync = providers.Callable(sync_snapshot, databricks_client, database_client, question_repo, config.provided.dbx_catalog)`).
- [ ] **Step 4:** Run → passed; `uv run python -c "from cortex_api.service.questions.container import Container; print(type(Container().job_service()).__name__)"` → `QuestionsJobService`; ruff+mypy clean.
- [ ] **Step 5:** Commit
```bash
git add api/src/cortex_api/service/questions/container.py api/tests/unit/test_questions_container.py
git commit -m "feat(sp-questions): questions DI container"
```

---

## Task 9: DTO + router + main.py wiring (gates per @owl #5)

**Files:** Create `app/api/questions/dto.py`, `router.py`; Modify `api/src/cortex_api/main.py`; Test `api/tests/integration/test_questions_api.py`.

- [ ] **Step 1:** Read `api/tests/integration/test_media_network_api.py` + conftest; write `tests/integration/test_questions_api.py` mirroring it: seed brand + brand_profile + a `weekly_question` row; mint a token with `["view_brand_dashboard","edit_brand_settings"]`; `POST /v1/brand/{bid}/weekly-questions` → 200/202; poll `GET` until `succeeded`; assert every item has `id`+`text`. Add `test_post_without_edit_capability_403` (token caps `["view_brand_dashboard"]` only → POST 403) and `test_cross_tenant_rejected` (token for another brand → 4xx). Hermetic: override the matcher via the container the same way the media API test does.
- [ ] **Step 2:** `cd api && uv run pytest tests/integration/test_questions_api.py -q -m integration` → FAIL.
- [ ] **Step 3:** Create `app/api/questions/dto.py` mirroring `app/api/media_network/dto.py`:
```python
# api/src/cortex_api/app/api/questions/dto.py
from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel

from cortex_api.service.questions.model.job import BrandWeeklyQuestions


class WeeklyQuestionsResponse(BaseModel):
    brand_id: UUID
    status: str
    questions: list[dict[str, Any]]
    error: str | None = None

    @classmethod
    def from_model(cls, m: BrandWeeklyQuestions) -> "WeeklyQuestionsResponse":
        return cls(brand_id=m.brand_id, status=m.status.value, questions=m.questions, error=m.error)
```
- [ ] **Step 4:** Create `app/api/questions/router.py` mirroring `app/api/media_network/router.py` — **POST gated `BrandCapability.EDIT_BRAND_SETTINGS`, GET gated `BrandCapability.VIEW_BRAND_DASHBOARD`** (spec D5); paths `POST/GET /v1/brand/{brand_id}/weekly-questions`; `active_brand` + `@inject` + `Provide[QuestionsContainer.job_service]`; call `svc.start(tenant.brand_id, regenerate=regenerate)` / `svc.get(tenant.brand_id)`; return `WeeklyQuestionsResponse.from_model`. Read the media router and copy its exact dependency import paths/decorator style; only the capability on POST (`EDIT_BRAND_SETTINGS`) and names differ.
- [ ] **Step 5:** Wire `main.py` mirroring the media container/router/lifespan (the 5/6-edit pattern): import `questions_router`, import `QuestionsContainer`, instantiate `_questions_container`, add to `_all_containers()`, `.wire(modules=["cortex_api.app.api.questions.router"])`+`include_router`, and add `_questions_container.job_service().sweep_stale()` to the periodic sweep + `cancel_all()` to shutdown — line-for-line like the media equivalents.
- [ ] **Step 6:** `cd api && uv run pytest tests/integration/test_questions_api.py tests/unit/test_app_boots.py -q` → pass; ruff+mypy clean on `app/api/questions` + `main.py`.
- [ ] **Step 7:** Commit
```bash
git add api/src/cortex_api/app/api/questions api/src/cortex_api/main.py api/tests/integration/test_questions_api.py
git commit -m "feat(sp-questions): weekly-questions endpoints + main.py wiring (POST=EDIT, GET=VIEW)"
```

---

## Task 10: Runnable sync entrypoint

**Files:** Create `api/scripts/sync_weekly_questions.py`.

- [ ] **Step 1:** Read `api/scripts/sync_media_network.py`; create the questions twin:
```python
# api/scripts/sync_weekly_questions.py
"""Run the Databricks->cortex weekly-question snapshot sync.
Usage: uv run python scripts/sync_weekly_questions.py"""
import asyncio

from cortex_api.service.questions.container import Container


async def _main() -> None:
    n = await Container().run_snapshot_sync()
    print(f"synced {n} weekly questions")


if __name__ == "__main__":
    asyncio.run(_main())
```
(Match the sibling's invocation/style exactly.)
- [ ] **Step 2:** Verify it imports: `cd api && uv run python -c "import ast; ast.parse(open('scripts/sync_weekly_questions.py').read()); from cortex_api.service.questions.container import Container; print('ok')"` (do NOT run the live sync).
- [ ] **Step 3:** Commit
```bash
git add api/scripts/sync_weekly_questions.py
git commit -m "feat(sp-questions): runnable weekly-question snapshot-sync entrypoint"
```

---

## Task 11: Web — projection + single-source DTO

**Files:** Modify `web/src/lib/cortex-api.ts`, `web/src/lib/onboarding/projection.ts`; Test `web/src/lib/onboarding/projection.test.ts` (extend).

- [ ] **Step 1: Failing test** (append to projection.test.ts):
```ts
import { projectWeeklyQuestions } from "./projection";

it("projectWeeklyQuestions maps real questions to LiveQuestion[]", () => {
  const dto = { brand_id: "b", status: "succeeded", questions: [
    { id: "a", text: "Best ETF?", media: "CMoney", asks: 300, when: "2026-05-15",
      intent: "Evaluate", score: 91, competitorMentions: ["Cathay"] }] };
  const q = projectWeeklyQuestions(dto);
  expect(q[0].id).toBe("a");
  expect(q[0].text).toBe("Best ETF?");
  expect(q[0].media).toBe("CMoney");
  expect(q[0].asks).toBe(300);
  expect(q[0].intent).toBe("Evaluate");
  expect(q[0].competitorMentions).toEqual(["Cathay"]);
});
```
- [ ] **Step 2:** `cd web && npx vitest run src/lib/onboarding/projection.test.ts` → FAIL.
- [ ] **Step 3:** In `web/src/lib/cortex-api.ts` add the canonical DTOs + start/poll fns by copying the `startMediaNetwork`/`pollMediaNetwork`/`MediaNetworkDTO`/`MediaOutletDTO` block verbatim and adapting: `WeeklyQuestionDTO = { id:string; text:string; media:string; asks:number; when:string; intent:string; score:number; competitorMentions:string[] }`, `WeeklyQuestionsDTO = { brand_id:string; status:string; questions:WeeklyQuestionDTO[]; error?:string|null }`, `startWeeklyQuestions(claims,brandId)` POST `/v1/brand/${brandId}/weekly-questions`, `pollWeeklyQuestions(claims,brandId)` GET same. Keep the exact token-signing/fetch/error shape used by the media fns.
- [ ] **Step 4:** In `web/src/lib/onboarding/projection.ts`: `import type { WeeklyQuestionsDTO } from "@/lib/cortex-api"` (single source — spec D6; mirror how `MediaNetworkDTO` is type-imported there), and add:
```ts
import type { LiveQuestion } from "@/components/onboarding-v2/data";

export function projectWeeklyQuestions(dto: WeeklyQuestionsDTO): LiveQuestion[] {
  return dto.questions.map((q) => ({
    id: q.id,
    text: q.text,
    media: q.media,
    intent: (["Explore", "Understand", "Evaluate", "Act"].includes(q.intent)
      ? q.intent : "Understand") as LiveQuestion["intent"],
    score: q.score,
    asks: q.asks ?? 0,
    when: q.when || "—",
    competitorMentions: q.competitorMentions ?? [],
  }));
}
```
(Match the existing `LiveQuestion` field names/types in `data.ts` exactly — read it; null-safe per spec D6.)
- [ ] **Step 5:** `cd web && npx vitest run src/lib/onboarding/projection.test.ts && npm run type-check && npx eslint src/lib/onboarding/projection.ts src/lib/cortex-api.ts` → pass/clean.
- [ ] **Step 6:** Commit
```bash
git add web/src/lib/cortex-api.ts web/src/lib/onboarding/projection.ts web/src/lib/onboarding/projection.test.ts
git commit -m "feat(sp-questions): web projection + single-source WeeklyQuestions DTO"
```

---

## Task 12: Web — seam + Server Actions + post-analyze wiring (EN + 繁中)

**Files:** Modify `web/src/lib/onboarding/api.ts`, `mock-api.ts`, `http-api.ts`; Create `web/src/app/(auth)/onboarding/v2/weekly-questions-actions.ts`; Modify `web/src/app/(auth)/onboarding/v2/page.tsx` + `.../zh-TW/page.tsx`, `web/src/components/onboarding-v2/step-questions.tsx` + `onboarding-v2-zh/step-questions.tsx`.

- [ ] **Step 1:** `OnboardingApi` interface (`web/src/lib/onboarding/api.ts`): add `getLiveQuestions(): Promise<LiveQuestion[]>`. `mock-api.ts`: implement returning the existing `LIVE_QUESTIONS` constant (import from `@/components/onboarding-v2/data`) — mock mode unchanged.
- [ ] **Step 2:** Create `weekly-questions-actions.ts` by copying `media-actions.ts` verbatim and renaming (`"use server"`, the SAME `claimsFromSession()` guard, `startWeeklyQuestionsAction`/`pollWeeklyQuestionsAction` calling the Task-11 `cortex-api.ts` fns). Read `media-actions.ts` and mirror exactly.
- [ ] **Step 3:** `http-api.ts`: implement `getLiveQuestions()` exactly like `getMediaNetwork()` (start → bounded poll loop → `projectWeeklyQuestions(dto)`; rethrow on failed/timeout). Mirror the media method.
- [ ] **Step 4:** EN `web/src/app/(auth)/onboarding/v2/page.tsx`: add `const [liveQuestions, setLiveQuestions] = useState<LiveQuestion[]>([])`; in `runAnalyze()`, AFTER the existing media `void (async()=>{…})()` block, add a **separate independent** block:
```ts
void (async () => {
  try {
    const lq = await api.getLiveQuestions();
    setLiveQuestions(lq);
  } catch {
    // non-fatal: analyze succeeded; step 4 simply shows no questions.
  }
})();
```
(do NOT add `getLiveQuestions` to `loadModeled` — spec D7); in `restart()` add `setLiveQuestions([])`; change the step-4 render to `{step === 4 && brand ? <StepQuestions brand={brand} liveQuestions={liveQuestions} /> : null}`.
- [ ] **Step 5:** Repeat Step 4 for 繁中 `web/src/app/(auth)/onboarding/v2/zh-TW/page.tsx` (same structure; keep 繁中 strings).
- [ ] **Step 6:** Make BOTH `step-questions.tsx` (EN `components/onboarding-v2/` + `onboarding-v2-zh/`) prop-driven: add `liveQuestions: LiveQuestion[]` to props, replace `const questions = LIVE_QUESTIONS` with `const questions = liveQuestions`, drop the `LIVE_QUESTIONS` import (keep `INTENT_COLOR`/other imports). **Preserve all 繁中 copy** in the zh file (only the data source changes).
- [ ] **Step 7:** `cd web && npm run type-check && npm run lint && npx vitest run src/lib/onboarding src/components/onboarding-v2 src/components/onboarding-v2-zh` → clean/pass (the pre-existing `page-load-states.test.tsx` `next/server` baseline may still fail — that ONE file only).
- [ ] **Step 8:** Commit
```bash
git add web/src/lib/onboarding/api.ts web/src/lib/onboarding/mock-api.ts web/src/lib/onboarding/http-api.ts "web/src/app/(auth)/onboarding/v2/weekly-questions-actions.ts" "web/src/app/(auth)/onboarding/v2/page.tsx" "web/src/app/(auth)/onboarding/v2/zh-TW/page.tsx" web/src/components/onboarding-v2/step-questions.tsx web/src/components/onboarding-v2-zh/step-questions.tsx
git commit -m "feat(sp-questions): web seam — getLiveQuestions post-analyze (EN+繁中), prop-driven StepQuestions"
```

---

## Task 13: Web — behavioral + structural call-site guard

**Files:** Create `web/src/components/onboarding-v2/__tests__/step-questions-real.test.tsx`, `web/src/app/(auth)/onboarding/v2/__tests__/orchestrator-questions-callsite.test.ts`.

- [ ] **Step 1:** Read `step-questions.tsx`'s real prop signature; write `step-questions-real.test.tsx` (mirror `step-media-real.test.tsx`): render `<StepQuestions brand={null as never} liveQuestions={[{id:"a",text:"REALQ?",media:"CMoney",intent:"Evaluate",score:90,asks:300,when:"—",competitorMentions:[]}]} />`; assert `REALQ?` rendered and an old `LIVE_QUESTIONS` mock string is absent.
- [ ] **Step 2:** Write `orchestrator-questions-callsite.test.ts` mirroring `orchestrator-media-callsite.test.ts` exactly but asserting, for BOTH `page.tsx` (EN) and `zh-TW/page.tsx`: `getLiveQuestions` ∉ the `loadModeled` region, ∈ the `runAnalyze` region, and its index is after `analyzeBrand`. (Read `orchestrator-media-callsite.test.ts` and clone its region-extraction helper + assertions.)
- [ ] **Step 3:** `cd web && npx vitest run src/components/onboarding-v2/__tests__/step-questions-real.test.tsx "src/app/(auth)/onboarding/v2/__tests__/orchestrator-questions-callsite.test.ts"` → pass.
- [ ] **Step 4:** Commit
```bash
git add "web/src/components/onboarding-v2/__tests__/step-questions-real.test.tsx" "web/src/app/(auth)/onboarding/v2/__tests__/orchestrator-questions-callsite.test.ts"
git commit -m "test(sp-questions): StepQuestions real-prop + orchestrator call-site guard (EN+繁中)"
```

---

## Task 14: Full gate parity + handoff

- [ ] **Step 1:** `cd api && make lint && make test` → ruff/format/mypy clean; all pytest pass (incl. `-m integration`).
- [ ] **Step 2:** Alembic round-trip: `cd api && uv run alembic upgrade head && uv run alembic downgrade e5f6a7b8c9d0 && uv run alembic upgrade head` → head `f6a7b8c9d0e1` (enum-drop gate clean).
- [ ] **Step 3:** `cd web && npm run type-check && npm run lint && npx vitest run` → type-check/lint clean; vitest all pass EXCEPT the documented pre-existing `page-load-states.test.tsx` baseline (no NEW failing file; `orchestrator-questions-callsite.test.ts` green).
- [ ] **Step 4:** `make format` if needed + commit fixups; then STOP and invoke `superpowers:finishing-a-development-branch` (push, open PR into `develop`; re-review via **`@owl review`** — `@owl verify` is infra-broken). The post-merge UAT deploy chain + the §7 future-refactor evaluation are separate follow-ups, NOT in this plan.

---

## Self-Review

**Spec coverage (D1–D9):** D1 → Task 6 SQL (`question_title`/`measure(question_clicks)`/`publisher_name`/`event_date` on `aigc_clickstream_metrics`). D2 ⊆-snapshot (`text`=verbatim title, media/asks/when from real row) → Task 5 matcher + Task 6 + Task 11 projection. D3 `competitorMentions` ⊆ real `brand_profile.competitors` → Task 5 (`competitors` set filter) + Task 7 (`BrandProfileRepo`). D4 intent/score LLM-derived → Task 5. D5 POST=`EDIT_BRAND_SETTINGS`/GET=`VIEW_BRAND_DASHBOARD` → Task 9. D6 single-source DTO + null-safe projection → Task 11. D7 d8345ff post-analyze, both EN+繁中, prop-driven, structural guard → Tasks 12–13. D8 empty→deterministic backfill / synth-grounded fallback → Task 5 (`_fallback`/backfill; matcher never raises) + spec note (LLM-synth-on-empty is the documented degraded path; v1 backfills from whatever snapshot exists, full-synth only if snapshot wholly empty — covered by the backfill loop + the matcher's no-raise contract). D9 Approach A clone + `BrandProfileRepo`/`_IDENTIFIER_RE` reuse → Tasks 2–9; §7 future-refactor noted in spec. Migration/round-trip → Task 3/14. Tests → every task TDD + Task 13 behavioral/guard + Task 14 parity.

**Placeholder scan:** No TBD/TODO. "RECONCILE" steps (Tasks 2,5,6,7,8,9,12,13) name the exact merged precedent file to mirror with the precise transformation stated — DRY "clone this proven file, change exactly these", not placeholders (the canonical code is on `develop`, not hypothetical).

**Type consistency:** `QuestionJobStatus`/`BrandWeeklyQuestions`/`WeeklyQuestion`(`id`,`question_title`,`publisher_name`,`clicks`,`last_event_date`) consistent T2/3/4/6/7/9. Matcher output keys (`id,text,media,asks,when,intent,score,competitorMentions`) consistent T5 ↔ DTO T9 ↔ projection T11 ↔ behavioral T13, and match the existing `LiveQuestion` shape. `QuestionsJobService.__init__(database_client, brand_questions_repo, question_repo, config, brand_profile_repo, provider, _match)` consistent T7 impl ↔ T7 test ↔ T8 container. Migration `f6a7b8c9d0e1` / `down_revision e5f6a7b8c9d0` consistent T3 ↔ T14. No drift.
