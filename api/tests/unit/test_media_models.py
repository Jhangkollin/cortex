# api/tests/unit/test_media_models.py
import uuid

from cortex_api.service.media_network.model.job import BrandMediaNetwork, MediaJobStatus
from cortex_api.service.media_network.model.member import MediaNetworkMember


def test_member_table():
    m = MediaNetworkMember(member_name="CMoney", hostname="aigc.cmoney.tw", wau=117260)
    assert m.hostname == "aigc.cmoney.tw"
    assert m.wau == 117260


def test_job_defaults():
    j = BrandMediaNetwork(brand_id=uuid.uuid4())
    assert j.status == MediaJobStatus.PENDING
    assert j.outlets == []
