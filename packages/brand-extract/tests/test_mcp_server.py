import pytest

pytest.importorskip("mcp")  # skip if [mcp] extra not installed

from cortex_brand_extract.mcp.server import build_server


async def test_server_registers_extract_tool() -> None:
    server = build_server()
    tools = await server.list_tools()
    names = {t.name for t in tools}
    assert "extract_brand_profile" in names
    assert "fetch_site" in names
