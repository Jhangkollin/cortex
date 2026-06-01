# api/tests/unit/test_media_config.py
from cortex_api.service.media_network.config import Config


def test_defaults():
    c = Config()
    assert c.outlet_count == 8
    assert c.stale_job_seconds == 180
    assert c.dbx_catalog == "aigc_prod"
