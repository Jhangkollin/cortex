# api/tests/unit/test_questions_matcher.py
from cortex_api.service.questions.matcher import match_questions
from cortex_api.service.questions.model.question import WeeklyQuestion


class FakeProvider:
    model = "fake"

    def __init__(self, payload):
        self._payload = payload

    async def complete_json(self, *, system, user, schema):
        from cortex_brand_extract.llm.base import LLMResult

        return LLMResult(data=self._payload)


class DispatchProvider:
    """Returns different payloads depending on which schema is requested.

    The snapshot-rank schema requires {id, intent, score, competitorMentions}
    per item; the D8 synth schema requires {text, intent, score, asks,
    competitorMentions}. We discriminate on whether `text` is in the item's
    `required` list.
    """

    model = "fake"

    def __init__(self, snapshot_payload=None, synth_payload=None, synth_raises=False):
        self._snapshot_payload = snapshot_payload if snapshot_payload is not None else {"questions": []}
        self._synth_payload = synth_payload if synth_payload is not None else {"questions": []}
        self._synth_raises = synth_raises

    async def complete_json(self, *, system, user, schema):
        from cortex_brand_extract.llm.base import LLMResult

        item_req = schema.get("properties", {}).get("questions", {}).get("items", {}).get("required", [])
        is_synth_call = "text" in item_req
        if is_synth_call and self._synth_raises:
            raise RuntimeError("synth LLM exploded")
        payload = self._synth_payload if is_synth_call else self._snapshot_payload
        return LLMResult(data=payload)


SNAP = [
    WeeklyQuestion(id="a", question_title="Best ETF for dividends?", publisher_name="CMoney", clicks=300),
    WeeklyQuestion(id="b", question_title="How to open USD account?", publisher_name="NOWnews", clicks=100),
]
PROFILE = {"name": "Acme Bank", "category": "Banking", "competitors": ["Cathay", "CTBC"], "products": [], "about": ""}


async def test_subset_enforced_and_competitor_subset():
    # question_count == len(SNAP) so D8 doesn't run — this test focuses on
    # the snapshot-rank pass's invariants (id ⊆ snapshot, competitorMentions
    # ⊆ profile.competitors). D8 has dedicated tests further below.
    prov = FakeProvider(
        {
            "questions": [
                {"id": "a", "intent": "Evaluate", "score": 90, "competitorMentions": ["Cathay", "FAKECORP"]},
                {"id": "ZZZ", "intent": "Act", "score": 80, "competitorMentions": []},
            ]
        }
    )
    out = await match_questions(PROFILE, SNAP, prov, question_count=2)
    ids = [q["id"] for q in out]
    assert "ZZZ" not in ids  # hallucinated id (not in snapshot) dropped
    a = next(q for q in out if q["id"] == "a")
    assert a["text"] == "Best ETF for dividends?" and a["media"] == "CMoney" and a["asks"] == 300
    assert a["intent"] in ("Explore", "Understand", "Evaluate", "Act")
    assert set(a["competitorMentions"]).issubset({"Cathay", "CTBC"})


async def test_empty_rank_routes_to_synth_not_topclicks():
    # When the rank LLM endorses nothing, the deficit is filled by brand-grounded
    # D8 synth, NOT by relevance-blind top-clicks from the pool. FakeProvider
    # returns the same empty payload for the synth call too, so D8's
    # deterministic placeholder emits — the point is the ids are synth-, never
    # the pool's "a"/"b".
    out = await match_questions(PROFILE, SNAP, FakeProvider({"questions": []}), question_count=2)
    assert len(out) == 2
    assert all(q["id"].startswith("synth-") for q in out), "empty rank must route to synth, not pool top-clicks"
    assert {q["id"] for q in out}.isdisjoint({"a", "b"})
    assert all(q["text"] and q["intent"] for q in out)


async def test_malformed_payload_never_raises():
    # Malformed rank payloads must never raise; the deficit routes to D8 synth
    # (FakeProvider returns the same malformed shape for the synth call, so D8's
    # deterministic placeholder fills the count).
    for bad in ({"questions": {"x": 1}}, {"questions": 42}, {"questions": [{"id": "a", "score": "NaN"}]}):
        out = await match_questions(PROFILE, SNAP, FakeProvider(bad), question_count=2)
        assert len(out) == 2
        assert all(q["text"] and q["intent"] for q in out)


async def test_truncated_to_count():
    prov = FakeProvider(
        {
            "questions": [
                {"id": "a", "intent": "Act", "score": 50, "competitorMentions": []},
                {"id": "b", "intent": "Act", "score": 40, "competitorMentions": []},
            ]
        }
    )
    out = await match_questions(PROFILE, SNAP, prov, question_count=1)
    assert len(out) == 1


# ---------------------------------------------------------------------------
# D8 — LLM-synth fallback when the snapshot can't satisfy question_count
# Per spec §3 D8: "If the snapshot is empty/stale for the 7-day window →
# documented LLM-synth fallback: synth N questions grounded in the real
# brand_profile (deterministic, persisted, clearly the fallback path)."
# ---------------------------------------------------------------------------

NIKE = {
    "name": "Nike Japan",
    "category": "Sportswear",
    "competitors": ["Adidas", "Puma", "Under Armour"],
    "products": [{"name": "Air Zoom Pegasus"}],
    "about": "Athletic footwear and apparel",
}


async def test_d8_synth_when_snapshot_empty():
    prov = DispatchProvider(
        synth_payload={
            "questions": [
                {
                    "text": "Best running shoe for marathon training?",
                    "intent": "Evaluate",
                    "score": 85,
                    "asks": 230,
                    "competitorMentions": ["Adidas"],
                },
                {
                    "text": "How do I choose shoes for flat feet?",
                    "intent": "Understand",
                    "score": 70,
                    "asks": 180,
                    "competitorMentions": [],
                },
            ]
        }
    )
    out = await match_questions(NIKE, [], prov, question_count=2)
    assert len(out) == 2
    assert all(q["text"] and q["intent"] in _INTENTS_TUPLE for q in out)
    assert all(q["id"].startswith("synth-") for q in out), "synth ids must be prefixed for traceability"
    mentions = {c for q in out for c in q["competitorMentions"]}
    assert mentions <= {"Adidas", "Puma", "Under Armour"}


async def test_d8_synth_competitor_mentions_strict_subset():
    prov = DispatchProvider(
        synth_payload={
            "questions": [
                {
                    "text": "Q",
                    "intent": "Act",
                    "score": 90,
                    "asks": 100,
                    "competitorMentions": ["Adidas", "FAKEBRAND"],
                }
            ]
        }
    )
    out = await match_questions(NIKE, [], prov, question_count=1)
    assert out[0]["competitorMentions"] == ["Adidas"], "FAKEBRAND (not in profile) must be filtered out"


async def test_d8_synth_never_raises_on_malformed_llm():
    # Provider raises mid-call AND returns garbage shapes — D8 must still return
    # question_count items so the wizard is never empty.
    cases = [
        DispatchProvider(synth_raises=True),
        DispatchProvider(synth_payload={"questions": "not a list"}),
        DispatchProvider(synth_payload={"questions": [{"text": None}]}),
        DispatchProvider(synth_payload={}),
    ]
    for prov in cases:
        out = await match_questions(NIKE, [], prov, question_count=3)
        assert len(out) == 3, "D8's deterministic fallback must emit question_count items"
        assert all(q["text"] for q in out)
        assert all(q["intent"] in _INTENTS_TUPLE for q in out)


async def test_d8_fills_deficit_after_partial_snapshot():
    """Snapshot has 1 item, LLM picks it, D8 fills the remaining 5."""
    snap = [WeeklyQuestion(id="x", question_title="Real Q", publisher_name="CMoney", clicks=200)]
    prov = DispatchProvider(
        snapshot_payload={"questions": [{"id": "x", "intent": "Act", "score": 90, "competitorMentions": []}]},
        synth_payload={
            "questions": [
                {"text": f"Synth Q{i}", "intent": "Understand", "score": 50, "asks": 100, "competitorMentions": []}
                for i in range(5)
            ]
        },
    )
    out = await match_questions(NIKE, snap, prov, question_count=6)
    assert len(out) == 6
    assert out[0]["id"] == "x", "real snapshot item ranks first"
    assert all(q["id"].startswith("synth-") for q in out[1:]), "remaining 5 are synth"


async def test_d8_not_called_when_snapshot_satisfies_count():
    """If the snapshot pick already gives us enough, D8 must NOT run."""
    snap = [
        WeeklyQuestion(id="a", question_title="A?", publisher_name="X", clicks=300),
        WeeklyQuestion(id="b", question_title="B?", publisher_name="Y", clicks=200),
    ]
    # Track whether the synth path was invoked by raising if it is
    prov = DispatchProvider(
        snapshot_payload={
            "questions": [
                {"id": "a", "intent": "Act", "score": 90, "competitorMentions": []},
                {"id": "b", "intent": "Evaluate", "score": 70, "competitorMentions": []},
            ]
        },
        synth_raises=True,  # any synth call → RuntimeError
    )
    # If D8 unnecessarily invoked, the matcher would catch the synth RuntimeError
    # via its broad except and emit deterministic synth placeholders. We assert
    # the output is pure-snapshot: no synth- ids at all.
    out = await match_questions(NIKE, snap, prov, question_count=2)
    assert {q["id"] for q in out} == {"a", "b"}, "must not invoke D8 when snapshot satisfies count"


async def test_irrelevant_pool_routes_to_synth_not_topclicks():
    """Regression for the Hamilton-watch UAT bug.

    The snapshot pool was Taiwanese news; the rank LLM endorsed nothing
    relevant; the OLD top-clicks backfill then filled every slot with globally
    popular but off-brand pool questions (politics, stocks), starving the D8
    synth path. The deficit must now route to brand-grounded synth, and the
    irrelevant pool questions must NOT appear.
    """
    pool = [
        WeeklyQuestion(id="n1", question_title="政治人物如何鞏固領導地位？", publisher_name="NOWnews", clicks=324),
        WeeklyQuestion(id="n2", question_title="三大法人賣超代表什麼？", publisher_name="Cmnews", clicks=171),
    ]
    hamilton = {
        "name": "Hamilton",
        "category": "Watches",
        "competitors": [],
        "products": [{"name": "Khaki Field"}],
        "about": "Swiss-made watch brand",
    }
    prov = DispatchProvider(
        snapshot_payload={"questions": []},  # ranker finds nothing relevant in a news pool
        synth_payload={
            "questions": [
                {
                    "text": "Which Khaki Field model suits everyday wear?",
                    "intent": "Evaluate",
                    "score": 88,
                    "asks": 210,
                    "competitorMentions": [],
                },
                {
                    "text": "How does an automatic movement keep time?",
                    "intent": "Understand",
                    "score": 75,
                    "asks": 150,
                    "competitorMentions": [],
                },
            ]
        },
    )
    out = await match_questions(hamilton, pool, prov, question_count=2)
    ids = {q["id"] for q in out}
    assert ids.isdisjoint({"n1", "n2"}), "irrelevant pool top-clicks must not be surfaced"
    assert all(q["id"].startswith("synth-") for q in out), "deficit must be filled by brand-grounded synth"
    texts = " ".join(q["text"] for q in out)
    assert "Khaki" in texts or "movement" in texts


async def test_low_relevance_picks_dropped_below_floor():
    """A pool question the ranker scores below the relevance floor is dropped,
    so a weak match doesn't crowd out brand-grounded synth."""
    prov = DispatchProvider(
        snapshot_payload={"questions": [{"id": "a", "intent": "Understand", "score": 10, "competitorMentions": []}]},
        synth_payload={
            "questions": [
                {"text": "Grounded synth?", "intent": "Act", "score": 90, "asks": 100, "competitorMentions": []}
            ]
        },
    )
    out = await match_questions(PROFILE, SNAP, prov, question_count=2)
    ids = {q["id"] for q in out}
    assert "a" not in ids, "score=10 is below the relevance floor and must be dropped"
    assert all(q["id"].startswith("synth-") for q in out)


# Keep this module-private so the assertion above stays self-contained
_INTENTS_TUPLE = ("Explore", "Understand", "Evaluate", "Act")
