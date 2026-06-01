# API contract

The authoritative contract is the OpenAPI spec served at `GET /openapi.json` from cortex-api. The TypeScript client in `web/src/lib/api-client/generated/` is regenerated from it.

## Regenerating

```bash
# From the cortex/ root:
make generate-client
```

This:
1. Runs cortex-api in-process to dump OpenAPI to `api/openapi.json`
2. Runs `@hey-api/openapi-ts` to regenerate `web/src/lib/api-client/generated/`

CI fails on drift (TODO: wire after first commit of generated client).

## Endpoint surface

| Path | Status | Domain |
|---|---|---|
| `GET /health`, `GET /version` | live | system |
| `GET /v1/auth/me` | implemented before this PR | auth / identity |
| `POST /v1/auth/resolve-context` | implemented for Brand before this PR; Publisher pending | auth / identity |
| `POST /v1/brand`, `GET /v1/brand/{brand_id}` | implemented before this PR | brand_identity |
| `GET /v1/brand/{brand_id}/analytics/metrics` | registered placeholder → live in Slice 1 | Brand Dashboard API projection over Insights |
| `GET /v1/brand/{brand_id}/analytics/metrics/by-publisher` | registered placeholder → live in Slice 4 | Brand Dashboard API projection over Insights |
| `GET /v1/publisher/{publisher_id}/analytics/metrics` | registered placeholder | Publisher Dashboard API projection over Insights |
| `POST /v1/kb/search` | placeholder | knowledge_base |
| `GET /v1/connectors` | placeholder | connectors |
| `GET /v1/admin/health` | placeholder | admin |

## Conventions

- All response models are Pydantic in `app/api/<domain>/dto.py`
- All routes use `response_model=` for OpenAPI completeness
- Errors are mapped from domain exceptions in `app/exception_handlers.py`
- Tenant scoping is implicit (resolved from JWT `active_context`), never a query param
