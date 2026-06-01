.PHONY: help install dev test lint format type-check clean docker-build generate-openapi

# =============================================================================
# Environment
# =============================================================================
ENV ?= uat
AWS_REGION := ap-northeast-1
ECR_REPO := aigc/cortex-api
IMAGE_NAME := cortex-api
VERSION := v0.1.0

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

# =============================================================================
# Local development
# =============================================================================

install: ## Install all deps via uv
	uv sync --all-extras

dev: ## Run dev server with reload
	uv run uvicorn cortex_api.main:app --reload --host 0.0.0.0 --port 8000

# =============================================================================
# Testing
# =============================================================================

test: ## Run tests with coverage
	uv run pytest --cov=cortex_api --cov-report=term-missing --cov-report=html

# =============================================================================
# Lint / format / type-check
# =============================================================================

lint: ## Ruff lint + format check + mypy
	uv run ruff check src tests
	uv run ruff format --check src tests
	uv run mypy src

format: ## Apply ruff format
	uv run ruff format src tests
	uv run ruff check --fix src tests

type-check: ## Run mypy only
	uv run mypy src

# =============================================================================
# OpenAPI
# =============================================================================

generate-openapi: ## Dump OpenAPI spec to openapi.json
	uv run python -c "import json; from cortex_api.main import app; print(json.dumps(app.openapi(), indent=2))" > openapi.json

# =============================================================================
# Docker
# =============================================================================

docker-build: ## Build container image
	docker build -t $(IMAGE_NAME):$(VERSION) .

# =============================================================================
# Database (Alembic)
# =============================================================================

migrate: ## Apply latest migrations
	uv run alembic upgrade head

migration-new: ## Create new revision (NAME=...)
	uv run alembic revision --autogenerate -m "$(NAME)"

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Remove caches and build artifacts
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
