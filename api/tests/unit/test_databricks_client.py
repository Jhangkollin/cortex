# api/tests/unit/test_databricks_client.py
import sys
import types

from cortex_api.infra.databricks_client import DatabricksClient


def test_run_query_uses_connector(monkeypatch):
    calls = {}

    class FakeCursor:
        def execute(self, sql, params=None):
            calls["sql"] = sql

        def fetchall(self):
            return [("CMoney", 117260)]

        def close(self):
            calls["cur_closed"] = True

    class FakeConn:
        def cursor(self):
            return FakeCursor()

        def close(self):
            calls["conn_closed"] = True

    fake_sql = types.SimpleNamespace(connect=lambda **kw: (calls.update(kw), FakeConn())[1])
    monkeypatch.setitem(sys.modules, "databricks", types.SimpleNamespace(sql=fake_sql))
    monkeypatch.setitem(sys.modules, "databricks.sql", fake_sql)

    c = DatabricksClient("h", "/sql/1.0/x", "cid", "csec")
    rows = c._run_query("select 1", {})
    assert rows == [("CMoney", 117260)]
    assert calls["server_hostname"] == "h" and calls["http_path"] == "/sql/1.0/x"
    assert calls["conn_closed"] and calls["cur_closed"]


def test_run_query_uses_m2m_credentials_provider_and_bare_hostname(monkeypatch):
    """The connect() call must use service-principal M2M auth.

    Passing bare ``client_id``/``client_secret`` kwargs to the connector does
    NOT select M2M — the databricks-sql-connector falls back to interactive
    U2M browser OAuth (an oauth localhost redirect), which can never work in a
    headless pod. M2M requires a ``credentials_provider`` callable. The
    connector also wants a bare ``server_hostname`` (no scheme / trailing
    slash), so the full ``CORE_DATABRICKS_HOST`` URL must be normalized.
    """
    calls = {}

    class FakeCursor:
        def execute(self, sql, params=None):
            calls["sql"] = sql

        def fetchall(self):
            return [(1,)]

        def close(self):
            pass

    class FakeConn:
        def cursor(self):
            return FakeCursor()

        def close(self):
            pass

    fake_sql = types.SimpleNamespace(connect=lambda **kw: (calls.update(kw), FakeConn())[1])

    # Fake the SDK so invoking the credentials_provider captures how Config is
    # built — exercising the producer, not just asserting a callable exists.
    cfg_calls: dict = {}

    class FakeConfig:
        def __init__(self, **kw):
            cfg_calls.update(kw)

    def fake_oauth_service_principal(config):
        cfg_calls["provider_built_from"] = config
        return "M2M_PROVIDER"

    fake_core = types.SimpleNamespace(Config=FakeConfig, oauth_service_principal=fake_oauth_service_principal)
    monkeypatch.setitem(
        sys.modules, "databricks", types.SimpleNamespace(sql=fake_sql, sdk=types.SimpleNamespace(core=fake_core))
    )
    monkeypatch.setitem(sys.modules, "databricks.sql", fake_sql)
    monkeypatch.setitem(sys.modules, "databricks.sdk", types.SimpleNamespace(core=fake_core))
    monkeypatch.setitem(sys.modules, "databricks.sdk.core", fake_core)

    c = DatabricksClient("https://dbc-xyz.cloud.databricks.com/", "/sql/1.0/x", "cid", "csec")
    c._run_query("select 1", {})

    # M2M via credentials_provider — NOT bare client_id/secret kwargs.
    cp = calls.get("credentials_provider")
    assert callable(cp)
    assert "client_id" not in calls
    assert "client_secret" not in calls
    # Hostname normalized to the bare host the connector expects.
    assert calls["server_hostname"] == "dbc-xyz.cloud.databricks.com"

    # Invoke the provider: it must build Config with the FULL URL host + the
    # real M2M creds, and hand it to oauth_service_principal. (A regression that
    # builds Config with the wrong field — e.g. token= — fails here, not silently
    # at runtime in-pod.)
    provider = cp()
    assert provider == "M2M_PROVIDER"
    assert cfg_calls["host"] == "https://dbc-xyz.cloud.databricks.com/"
    assert cfg_calls["client_id"] == "cid"
    assert cfg_calls["client_secret"] == "csec"
