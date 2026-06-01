"""Weekly-questions API integration tests.

Mirrors ``test_media_network_api.py`` exactly: same TestClient-inside-cm pattern,
same ``_authed`` / ``make_client`` + DI-provider override approach, same
cross-tenant rejection probe.

The matcher (``_match``) is overridden via DI container override on
``QuestionsContainer.job_service`` with a ``QuestionsJobService``
whose ``_match`` is a deterministic in-process fake — no network, no LLM,
no mock.patch. The brand_profile and weekly_question rows are seeded
inside the TestClient portal loop so the in-process worker's DB reads see
them.
"""

from __future__ import annotations

import contextlib
import uuid

import pytest
from fastapi.testclient import TestClient

from cortex_api.app.dependencies.auth import authenticated_user
from cortex_api.core.identifiers import uuid7
from cortex_api.infra.container import Container as InfraContainer
from cortex_api.main import create_app
from cortex_api.service.brand.model.profile import BrandProfile
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.brand_identity.model.brand import Brand
from cortex_api.service.identity.model.authed_user import AuthedUser
from cortex_api.service.questions.config import Config as QuestionsConfig
from cortex_api.service.questions.job_service import QuestionsJobService
from cortex_api.service.questions.model.question import WeeklyQuestion
from cortex_api.service.questions.repo.brand_questions_repo import BrandQuestionsRepo
from cortex_api.service.questions.repo.question_repo import QuestionRepo

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
async def _schema():
    from sqlmodel import SQLModel

    db = InfraContainer()._database_client_factory()
    async with db.session() as s:
        conn = await s.connection()
        await conn.run_sync(SQLModel.metadata.create_all)


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


async def _fake_match(profile, snapshot, provider, question_count, min_relevance_score=40):
    """Deterministic in-process matcher — no network, no LLM, no mock.patch."""
    return [
        {
            "id": q.id,
            "text": q.question_title,
            "media": q.publisher_name,
            "asks": q.clicks,
            "when": "",
            "intent": "Understand",
            "score": 80,
            "competitorMentions": [],
        }
        for q in snapshot[:question_count]
    ]


async def _seed(db, bid) -> None:
    """Seed brand + brand_profile + at least one weekly_question row."""
    async with db.session() as s:
        s.add(Brand(id=bid, display_name="QuestionsApiCo"))
        await s.flush()
        # brand_profile row — job._run reads it via BrandProfileRepo
        await BrandProfileRepo().upsert(s, BrandProfile(brand_id=bid, name="QuestionsApiCo"))
        # At least one snapshot question so the matcher has something to rank
        await QuestionRepo().upsert_all(
            s,
            [WeeklyQuestion(id="q-test-1", question_title="What is AI?", publisher_name="TechMedia", clicks=100)],
        )


@pytest.fixture
def make_client():
    """Yield a ``make_client(*, jwt_brand_id=None, caps=None)`` factory cm.

    Mirrors ``test_media_network_api.py``'s ``make_client``:
    - builds the real app via ``create_app()``;
    - overrides ``authenticated_user`` with a brand-scoped ``AuthedUser``;
    - overrides the app's ``QuestionsContainer.job_service`` with a
      ``QuestionsJobService`` whose ``_match`` is the deterministic fake;
    - yields inside ``with TestClient(app) as c:`` (NOT a bare
      ``TestClient(app)``).
    """
    from cortex_api import main as _main

    overridden = False

    @contextlib.contextmanager
    def _factory(*, jwt_brand_id=None, caps=None):
        nonlocal overridden
        app = create_app()

        bid = uuid7()
        db = _main._questions_container.database_client()
        fake_service = QuestionsJobService(
            database_client=db,
            brand_questions_repo=BrandQuestionsRepo(),
            question_repo=QuestionRepo(),
            config=QuestionsConfig(),
            brand_profile_repo=BrandProfileRepo(),
            provider=object(),
            _match=_fake_match,
        )
        _main._questions_container.job_service.override(fake_service)
        overridden = True

        token_brand = jwt_brand_id if jwt_brand_id is not None else bid
        token_caps = caps if caps is not None else ["view_brand_dashboard", "edit_brand_settings"]
        app.dependency_overrides[authenticated_user] = lambda: _authed(
            token_brand,
            token_caps,
        )

        with TestClient(app) as c:
            # Seed inside the portal loop so the worker's reads see the rows.
            c.portal.call(_seed, db, bid)
            yield c, bid

    try:
        yield _factory
    finally:
        if overridden:
            _main._questions_container.job_service.reset_override()


def test_post_weekly_questions_then_get_succeeds(make_client) -> None:
    """POST starts the job (202 or 200), polling GET eventually yields succeeded."""
    with make_client() as (client, brand_id):
        r = client.post(f"/v1/brand/{brand_id}/weekly-questions")
        assert r.status_code in (200, 202), r.text
        body = {}
        for _ in range(50):
            g = client.get(f"/v1/brand/{brand_id}/weekly-questions")
            assert g.status_code == 200, g.text
            body = g.json()
            if body["status"] in ("succeeded", "failed"):
                break
        assert body["status"] == "succeeded", body
        assert all("id" in q and "text" in q for q in body["questions"]), body["questions"]


def test_post_without_edit_capability_403(make_client) -> None:
    """A token missing EDIT_BRAND_SETTINGS must be refused on POST."""
    with make_client(caps=["view_brand_dashboard"]) as (client, brand_id):
        r = client.post(f"/v1/brand/{brand_id}/weekly-questions")
        assert r.status_code == 403, r.text


def test_cross_tenant_rejected(make_client) -> None:
    """JWT scoped to brand A hitting brand B's weekly-questions URL → 4xx.

    Mirrors ``test_media_network_api.py``'s ``test_cross_tenant_rejected``:
    a single make_client context mints a token for a DIFFERENT brand id
    (``jwt_brand_id=uuid4()``) while the seeded brand is the URL target.
    ``active_brand`` sees a JWT brand ≠ URL brand and raises ContextMismatchError
    → mapped to 400 by the exception handler.
    """
    other = uuid.uuid4()
    with make_client(jwt_brand_id=other) as (client, seeded_bid):
        # JWT is for `other`, but the URL targets the seeded brand → mismatch
        g = client.get(f"/v1/brand/{seeded_bid}/weekly-questions")
        assert 400 <= g.status_code < 500, g.text
