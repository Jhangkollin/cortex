# Cortex

Green-field insights dashboard product for Mlytics — Brand and Publisher views, internally hosted, deployed on AWS EKS in Tokyo.

## Layout

```
cortex/
├── api/         FastAPI service (cortex-api)
├── web/         Next.js 16 dashboard (cortex-web)
├── docs/        architecture, auth, identity model, domain docs
└── .github/     CI workflows (build + ECR push)
```

Deploy config lives in `../infra/` (Helm charts + Terraform), not in this repo.

## Quick start

```bash
# Backend
cd api
uv sync
uv run uvicorn cortex_api.main:app --reload --port 8000

# Frontend (separate terminal)
cd web
npm install
npm run dev

# Local dependencies (postgres + redis)
docker-compose up
```

## Product Surfaces

| Surface | Status |
|---|---|
| shared kernel | target — OrgId/UserId/PersonaType/Money/Jurisdiction |
| identity foundation | MVP shipped Brand-first; target Org/AppUser/OrgMembership |
| brand / publisher actors | Brand MVP, Publisher scaffolded |
| discovery / placement / agent | target capability contexts |
| library | target versioned asset context |
| insights | MVP — persona-neutral Databricks read-model primitives |
| Brand Dashboard API projection | MVP — flagship |
| Publisher Dashboard API projection | placeholder |
| knowledge_base | placeholder, superseded by Library when versioned assets land |
| connectors | placeholder |
| admin | placeholder (future PHP replacement) |

## Documentation

- `docs/architecture.md` — high-level architecture
- `docs/auth.md` — OAuth + JWT flow
- `docs/identity-model.md` — orgs, users, roles, capabilities
- `docs/api-contract.md` — OpenAPI snapshot
- `docs/deploy.md` — deploy boundary (cortex repo vs `../infra/`)
- `docs/domains/` — per-domain READMEs

## See also

- `../aigc_coordinator/cortex-scaffolding-design.md` — full scaffolding design
- `../aigc_coordinator/cortex-mvp-plan.md` — MVP delivery plan with feature slices
