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
