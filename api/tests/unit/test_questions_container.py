# api/tests/unit/test_questions_container.py
from cortex_api.service.questions.container import Container


def test_container_provides_service_and_sync():
    c = Container()
    assert c.job_service() is not None
    assert callable(c.run_snapshot_sync)
