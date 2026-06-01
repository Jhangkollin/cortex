# api/tests/unit/test_media_container.py
from cortex_api.infra.container import Container as InfraContainer
from cortex_api.infra.databricks_client import DatabricksClient
from cortex_api.service.media_network.container import Container


def test_infra_databricks_factory():
    assert isinstance(InfraContainer()._databricks_client_factory(), DatabricksClient)


def test_container_provides_service_and_sync():
    c = Container()
    assert c.job_service() is not None
    assert callable(c.run_snapshot_sync)
