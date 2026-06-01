"""Entrypoint: `python -m cortex_brand_extract.mcp` (stdio transport)."""

from __future__ import annotations

from cortex_brand_extract.mcp.server import build_server


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
