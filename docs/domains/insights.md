# Insights Read Model

Insights is the stateless CQRS read model from Okis' domain map. It is not a
DDD bounded context per persona. Brand, Publisher, Developer, and future
persona dashboards should consume common Insights primitives and apply
persona-specific shaping at the API/app boundary.

## Boundary

| Belongs here | Stays persona-specific |
|---|---|
| Metric snapshot shape (`value`, `delta_pct`, `points`) | KPI labels and copy |
| Time range parsing | Route prefix and tenant dependency |
| Generic metric-set container | Metric catalogs |
| Shared cache/key/query helpers once reused | Capability names |
| Databricks row mapping patterns once reused | Which gold tables are queried |
| | Which breakdown dimension is default in the UI |

Insights does not own a source-of-truth aggregate; it reads Databricks gold
tables and projects the result into immutable Pydantic value objects. Every
Insights query is scoped by the active `OrgId` / persona context resolved by
Identity dependencies.

## Projection Pattern

Brand MVP currently exposes:

- `/v1/brand/{brand_id}/analytics/metrics`
- `/v1/brand/{brand_id}/analytics/metrics/by-publisher`

Those routes are Brand Dashboard API projection surfaces. Brand-specific
choices currently live in `service/brand_dashboard/` as a thin adapter; shared
read-model behavior belongs in `service/insights/`.

When the Publisher Dashboard projection begins, do **not** copy the Brand
Dashboard package. Start from the shared Insights primitives, define the
Publisher metric catalog at the projection edge, and add only the
Publisher-specific adapter and DTO mapping.

Do not add generic funnel or breakdown value objects until a second projection
actually consumes the same shape. Until then, Brand-specific names such as
`PublisherBreakdown` are clearer than a speculative generic model.
