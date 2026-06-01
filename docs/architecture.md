# Architecture

Cortex is two services on AWS EKS in Tokyo (`ap-northeast-1`):

```
                 [Internet · Cloudflare]
                          │
                          ▼
                 [ALB · cortex.internal.mlytics.com]
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
     [cortex-web pod]            [cortex-api pod]
     Next.js 16 (RSC)           FastAPI + DI
            │                           │
            │ GET /v1/...                │
            └─────────────┬─────────────┘
                          │
                  ┌───────┴────────┐
                  ▼                ▼
             [RDS Postgres]    [ElastiCache]
             identity:         cache layer
             - app_user
             - brand
             - brand_membership
             - future publisher tables
                          │
                          ▼
                  [Databricks SQL Warehouse]
                  (filtered by active context id)
                          │
                          ▼
                  [Databricks Vector Search]
                  (filtered by vector_namespace)
```

> **OLTP = AWS RDS PostgreSQL**. Original plan was Databricks Lakebase (single auth surface, all-Databricks ecosystem) but Lakebase isn't released in `ap-northeast-1` yet. Drivers / SQLModel / Alembic are Postgres-generic, so swapping to Lakebase later is essentially a DSN change.

## Two services, one repo

Cortex uses a monorepo (`cortex/`) with two service folders (`api/` and `web/`) that build into separate EKS pods.

- **`api/`** — Python 3.12, FastAPI, three-tier DI. Mirrors agent-will-smith conventions.
- **`web/`** — Next.js 16 App Router. NextAuth + Google OAuth.

## Tenant scoping

Every protected request resolves scope from the JWT's `active_context`.
FastAPI dependencies validate the token and assert the requested route matches
the active Brand or Publisher context:

- `authenticated_user` validates the bearer token
- `active_brand` returns `BrandTenantCtx` and asserts `active_context.kind == "brand"`
- `active_publisher` returns `PublisherTenantCtx` and asserts `active_context.kind == "publisher"`
- `requires_brand_capability(...)` / `requires_publisher_capability(...)` gate actions

Every Databricks query and every vector search filters by the active context id
from these dependencies. **Never** trust client-supplied tenant scope.

## Insights Read Model

Insights is the shared CQRS read model over Databricks gold tables. Brand and
Publisher dashboards are API/app projections over common metric, funnel,
cohort, digest, prediction, recommendation, and cache behavior. The current
Brand Dashboard adapter reads Brand-scoped gold tables; future Publisher work
should reuse `service/insights/` rather than cloning Brand code.

## Frontend rendering rule

`web/src/lib/permissions.ts` defines context-role capabilities for frontend
UX. The backend re-validates capabilities on every request — frontend
permissions are UX, not security.

## Deploy boundary

The `cortex/` repo builds container images and pushes to ECR. Deploy config (Helm + Terraform + Pod Identity) lives in `../infra/`. See `deploy.md`.
