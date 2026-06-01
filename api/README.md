# cortex-api

FastAPI service powering Cortex's insights-backed dashboards. Mirrors agent-will-smith's three-tier DI pattern.

## Layout

```
src/cortex_api/
├── main.py            entry: container wiring + router registration
├── core/              configs, exceptions, logger, CoreContainer
├── infra/             database / databricks / redis / vector search clients + InfraContainer
├── service/           business domains + read-side projections
└── app/               FastAPI surface (middleware, routers, DTOs)
```

## Quick start

```bash
uv sync
docker-compose up -d  # local postgres + redis
cp .env.example .env  # fill in Databricks creds
uv run alembic upgrade head
uv run uvicorn cortex_api.main:app --reload --port 8000
```

Open http://localhost:8000/docs for the OpenAPI UI.

## Common commands

```bash
make test            # pytest with coverage
make lint            # ruff + mypy
make format          # apply ruff format
make migrate         # alembic upgrade head
make migration-new NAME="add foo"
make generate-openapi
```

## Tests

```bash
uv run pytest -m "not integration"   # unit suite (default; no DB required)
uv run pytest -m integration         # integration suite (needs Postgres)
uv run pytest                        # both, if Postgres is reachable
```

Integration tests boot the FastAPI app against a real Postgres and exercise
the auth + brand-creation flow end-to-end. See `tests/integration/README.md`
for fixtures, local-run instructions, and CI wiring.

## Conventions

See `../CLAUDE.md` for repo-wide rules. Domain pattern follows `../../agent-will-smith/`:

- DI: `CoreContainer → InfraContainer → ServiceContainer`, wired in `main.py` only
- All exceptions from `core/exceptions.py`, chain with `from e`
- Logger: `structlog.get_logger(__name__)` in `__init__`
- Config: Pydantic `BaseSettings` with `env_prefix`
- Middleware: pure ASGI only
- Tests: override DI providers, never `mock.patch`
