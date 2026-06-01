import uuid

from cortex_api.service.voice.model.job import BrandVoice, VoiceJobStatus


def test_job_defaults():
    j = BrandVoice(brand_id=uuid.uuid4())
    assert j.status == VoiceJobStatus.PENDING
    assert j.samples == {}
