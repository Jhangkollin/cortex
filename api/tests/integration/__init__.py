"""Integration test suite — exercises the FastAPI app + DI containers
against a real Postgres. Run via `pytest -m integration` (requires
docker-compose up postgres or a CORE_DB_* env pointing at a reachable DB).

See `conftest.py` for fixtures and `README.md` (this directory) for
local-run instructions.
"""
