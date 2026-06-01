# api/scripts/sync_weekly_questions.py
"""Run the Databricks->cortex weekly-question snapshot sync.

Usage (out-of-band; requires Databricks creds in the environment):
    uv run python scripts/sync_weekly_questions.py
"""
import asyncio

from cortex_api.service.questions.container import Container


async def _main() -> None:
    n = await Container().run_snapshot_sync()
    print(f"synced {n} weekly questions")


if __name__ == "__main__":
    asyncio.run(_main())
