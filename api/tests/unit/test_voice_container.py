from cortex_api.service.voice.container import Container


def test_container_provides_service():
    c = Container()
    assert c.job_service() is not None
