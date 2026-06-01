# Integration tests

End-to-end tests that boot the FastAPI app + dependency-injector containers
against a **real Postgres**. Catches the class of bugs that only show up
once the DB constraint engine is involved (partial UNIQUE indexes, async
session lifecycles, FK CASCADEs, JWT shape contracts across the web/api
boundary).

Unit tests live in `../unit/` and run on every `pytest` invocation. Integration
tests are gated by the `integration` marker so contributors without Postgres
can still run the unit suite (`pytest -m "not integration"`).

## Running locally

```bash
cd api
# 1) Start local Postgres (docker-compose maps host 5433 → container 5432)
docker-compose up -d postgres

# 2) Ensure env points at it (defaults already match docker-compose.yml)
#    or override with a one-knob DSN:
#    export CORTEX_TEST_DB_URL=postgresql+asyncpg://cortex:cortex@localhost:5433/cortex

# 3) Run
uv run pytest -m integration
```

The suite automatically runs `alembic upgrade head` once per session, then
`TRUNCATE brand_membership, brand, app_user CASCADE` between tests — no
manual reset needed.

## Skipping when DB isn't available

```bash
uv run pytest -m "not integration"
```

This is what `make test` defaults to in environments without Postgres.

## Required env

| Var | Default | Notes |
|---|---|---|
| `CORE_DB_HOST` | `localhost` | matches `docker-compose.yml` |
| `CORE_DB_PORT` | `5433` | docker-compose maps :5433 to avoid Homebrew Postgres conflict |
| `CORE_DB_USERNAME` | `cortex` | |
| `CORE_DB_PASSWORD` | `cortex` | |
| `CORE_DB_NAME` | `cortex` | |
| `CORE_AUTH_NEXTAUTH_SECRET` | `change-me` | tests sign + verify with the same value |
| `CORTEX_TEST_DB_URL` | — | optional one-knob override, parsed back into CORE_DB_* |

## CI

`.github/workflows/ci.yml` adds a Postgres 16 service container to the api job
and runs unit tests + integration tests as two consecutive steps. Failing one
fails the job; the unit step runs first so a missing DB doesn't mask logic bugs.

## Adding a test

1. Pick a regression you actually want to pin. Don't reproduce unit-level
   coverage here — those belong in `tests/unit/`.
2. Decorate the module with `pytestmark = pytest.mark.integration` (or each
   function individually).
3. Use the `client`, `bootstrap_jwt`, `session_jwt`, `db_engine` fixtures
   from `conftest.py`. The DB starts empty for every test.
4. If you need a different starting state, INSERT through the same
   TestClient calls — don't fixture-INSERT directly via `db_engine` unless
   you're asserting the structure of an already-populated DB.
