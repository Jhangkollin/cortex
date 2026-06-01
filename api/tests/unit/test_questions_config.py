# api/tests/unit/test_questions_config.py
from cortex_api.service.questions.config import Config


def test_defaults():
    c = Config()
    assert c.question_count == 6
    assert c.stale_job_seconds == 180
    assert c.dbx_catalog == "aigc_prod"
    assert c.min_relevance_score == 40
