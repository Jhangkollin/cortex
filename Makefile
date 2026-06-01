.PHONY: help test test-api test-web lint lint-api lint-web generate-client docker-build docker-push build-local build-local-api build-local-web clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

# =============================================================================
# Tests
# =============================================================================

test: test-api test-web ## Run all tests

test-api: ## Run api/ tests
	cd api && make test

test-web: ## Run web/ tests
	cd web && npm test

# =============================================================================
# Lint
# =============================================================================

lint: lint-api lint-web ## Lint everything

lint-api: ## Lint api/ (ruff + mypy)
	cd api && make lint

lint-web: ## Lint web/ (eslint + tsc)
	cd web && npm run lint && npm run type-check

# =============================================================================
# OpenAPI client generation
# =============================================================================

generate-client: ## Regen TypeScript client from cortex-api OpenAPI
	cd api && uv run python -m cortex_api.scripts.dump_openapi > openapi.json
	cd web && npx @hey-api/openapi-ts \
		--input ../api/openapi.json \
		--output src/lib/api-client/generated \
		--client @hey-api/client-fetch

# =============================================================================
# Docker
# =============================================================================

docker-build: ## Build both api/ and web/ images
	cd api && make docker-build
	cd web && docker build -t cortex-web:dev .

# =============================================================================
# Local build + push to UAT ECR (GitHub Actions outage workaround)
# =============================================================================
#
# Mirrors .github/workflows/deploy.yml when CI dispatch is unavailable. Tags
# with `git rev-parse --short HEAD` by default. Pushes BOTH images to the UAT
# ECR account (147997115496) as `linux/arm64` (the Graviton cluster's arch).
#
# Critical flags (don't drop):
#   --platform linux/arm64       — UAT EKS nodes are Graviton; amd64 crashes
#                                  pods with "exec format error".
#   --provenance=false --sbom=false
#                                — the default buildx attestation adds an
#                                  unknown/unknown manifest entry that EKS
#                                  containerd rejects with "no match for
#                                  platform in manifest: not found".
#
# Requires:
#   - Apple Silicon (arm64 native, no QEMU) or a host with linux/arm64 buildx
#     support registered (`docker buildx ls` shows linux/arm64).
#   - Active AWS SSO session for profile c2g-uat (`aws sso login --profile c2g-uat`).

BUILD_LOCAL_ECR_UAT := 147997115496.dkr.ecr.ap-northeast-1.amazonaws.com
BUILD_LOCAL_AWS_PROFILE ?= c2g-uat
BUILD_LOCAL_PLATFORM := linux/arm64
BUILD_LOCAL_TAG ?= $(shell git rev-parse --short HEAD)

build-local: build-local-api build-local-web ## Build + push both images to UAT ECR (Actions outage). Override tag with TAG=<sha>.
	@echo ""
	@echo "Pushed:"
	@echo "  $(BUILD_LOCAL_ECR_UAT)/agents/cortex-api:$(BUILD_LOCAL_TAG)"
	@echo "  $(BUILD_LOCAL_ECR_UAT)/agents/cortex-web:$(BUILD_LOCAL_TAG)"
	@echo ""
	@echo "Verify arch (must show 'arm64/linux'):"
	@for repo in cortex-api cortex-web; do \
		docker pull $(BUILD_LOCAL_ECR_UAT)/agents/$$repo:$(BUILD_LOCAL_TAG) >/dev/null; \
		arch=$$(docker image inspect $(BUILD_LOCAL_ECR_UAT)/agents/$$repo:$(BUILD_LOCAL_TAG) --format '{{.Architecture}}/{{.Os}}'); \
		echo "  $$repo:$(BUILD_LOCAL_TAG) -> $$arch"; \
		case "$$arch" in arm64/linux) ;; *) echo "  ERROR: expected arm64/linux"; exit 1 ;; esac; \
	done
	@echo ""
	@echo "Next: bump environments/uat/cortex/values.yaml in data-platform-helm-charts."
	@echo "Pin by digest if a kubelet cache risk exists (see git history of"
	@echo "values.yaml for the e7573f0 digest-pin example)."

build-local-api: build-local-login
	docker buildx build \
		--platform $(BUILD_LOCAL_PLATFORM) \
		--provenance=false \
		--sbom=false \
		-t $(BUILD_LOCAL_ECR_UAT)/agents/cortex-api:$(BUILD_LOCAL_TAG) \
		-f api/Dockerfile \
		--push \
		.

build-local-web: build-local-login
	docker buildx build \
		--platform $(BUILD_LOCAL_PLATFORM) \
		--provenance=false \
		--sbom=false \
		-t $(BUILD_LOCAL_ECR_UAT)/agents/cortex-web:$(BUILD_LOCAL_TAG) \
		--build-arg NEXT_PUBLIC_CORTEX_ONBOARDING_HTTP=1 \
		--push \
		web/

build-local-login:
	@aws ecr get-login-password --region ap-northeast-1 --profile $(BUILD_LOCAL_AWS_PROFILE) \
		| docker login --username AWS --password-stdin $(BUILD_LOCAL_ECR_UAT) >/dev/null

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Remove generated artifacts and caches
	cd api && make clean
	cd web && rm -rf .next out node_modules
