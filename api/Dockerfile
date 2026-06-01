# syntax=docker/dockerfile:1.7

FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy

# Install uv
RUN pip install --no-cache-dir uv==0.4.30

# Build the venv where it will live in the runtime image. uv encodes the
# absolute venv path into every script's shebang at sync time (e.g.
# .venv/bin/uvicorn -> `#!/app/api/.venv/bin/python`). Building elsewhere then
# copying would leave broken shebangs and fail with the misleading
# `exec ... no such file or directory` (the ENOENT is on the interpreter,
# not the script). Same path also makes the editable install of cortex_api
# resolve correctly at runtime.
#
# The build context is the repo ROOT (see deploy.yml: `-f api/Dockerfile .`),
# because api/uv.lock pins the cortex-brand-extract dependency as an editable
# path `../packages/brand-extract`. The in-image layout must mirror the repo so
# that relative path resolves: WORKDIR is /app/api and the package is copied to
# its sibling /app/packages/brand-extract (i.e. ../packages/brand-extract).
WORKDIR /app/api

# README.md is required by hatchling's validate_fields() at `uv sync` time
# because pyproject.toml declares `readme = "README.md"`. Keep this COPY line
# in sync with any [project] field that references a file (readme, license,
# license-files). Trimming README.md here without updating pyproject.toml
# will re-break the build with `OSError: Readme file does not exist`.
#
# The editable cortex-brand-extract source must exist at the uv.lock-pinned
# relative path before `uv sync --frozen` runs; copy it to the WORKDIR sibling.
COPY packages/brand-extract /app/packages/brand-extract
COPY api/pyproject.toml api/uv.lock* api/README.md ./
COPY api/src ./src

RUN uv sync --frozen --no-dev

# ---

FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/api/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    # CJK fonts for PDF rendering (Noto CJK TC/SC). Adds ~150 MB.
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/api

# Preserve the builder's absolute layout: venv shebangs encode
# /app/api/.venv/bin/python, and the editable installs resolve cortex_api from
# /app/api/src and cortex-brand-extract from /app/packages/brand-extract.
COPY --from=builder /app/api/.venv /app/api/.venv
COPY --from=builder /app/api/src /app/api/src
COPY --from=builder /app/packages/brand-extract /app/packages/brand-extract

# Install Playwright Chromium headless shell + its system deps.
# This adds ~300 MB; total image grows from ~350 MB to ~800 MB.
# The --no-sandbox flag in renderer.py is required in containerised environments.
#
# PLAYWRIGHT_BROWSERS_PATH pins the browser to a shared, world-readable path
# instead of the installing user's $HOME/.cache. We must install as root (for
# --with-deps apt), but the container runs as the non-root `cortex` user at
# runtime — whose $HOME (/home/cortex) is NOT where a root install lands
# (/root/.cache). Without this pin, runtime fails with "Executable doesn't
# exist at /home/cortex/.cache/ms-playwright/...". Setting it as an ENV (not a
# build-only var) persists it into the running process so Playwright resolves
# the browser from /ms-playwright; `chmod a+rX` makes that tree readable and
# traversable by the cortex user.
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN /app/api/.venv/bin/playwright install --with-deps chromium \
    && chmod -R a+rX /ms-playwright \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

RUN useradd -r -u 1000 cortex && chown -R cortex:cortex /app
USER cortex

# Build-time guard (fail-fast / dev-prod parity): assert the *cortex* runtime
# user can resolve the Chromium binary at the pinned path. This fails the BUILD
# if the root-install / non-root-runtime / $HOME mismatch ever regresses (the
# COR-80 bug), instead of surfacing as a UAT 500 on a customer PDF request. Runs
# after USER cortex so it checks the identity that actually serves requests.
RUN python -c "import os, sys; from playwright.sync_api import sync_playwright; \
pw = sync_playwright().start(); exe = pw.chromium.executable_path; pw.stop(); \
print('chromium executable:', exe); \
sys.exit(0 if exe.startswith('/ms-playwright') and os.path.exists(exe) else 1)"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

CMD ["uvicorn", "cortex_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
