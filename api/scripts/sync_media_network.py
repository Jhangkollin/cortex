# api/scripts/sync_media_network.py
"""Run the Databricks->cortex media-network snapshot sync.

Usage (out-of-band; requires Databricks creds in the environment):
    uv run python scripts/sync_media_network.py
"""
import asyncio

from cortex_api.service.media_network.container import Container


async def _main() -> None:
    n = await Container().run_snapshot_sync()
    print(f"synced {n} media members")


if __name__ == "__main__":
    asyncio.run(_main())
