from cortex_api.service.voice.config import Config


def test_defaults():
    c = Config()
    assert c.stale_job_seconds == 180
