# Insights Read Model

Shared Insights primitives live here. This package is **not** a tenant bounded
context; it is the CQRS read side over Databricks gold tables from Okis'
domain model.

Use this package for logic and value objects that are identical across Brand,
Publisher, Developer, or future persona dashboards:

- time ranges (`7d`, `30d`, `90d`, `mtd`)
- metric snapshots (`value`, `delta_pct`, `points`)
- generic metric sets keyed by a persona-owned metric enum
- cache-key conventions once a second projection needs the same key shape
- Databricks gold-table row mapping patterns once a second projection consumes them

Persona-specific dashboard adapters should stay thin: they own their metric
catalog, enforce the active tenant type, and map shared Insights models to
route-specific DTOs. Do not copy a Brand Dashboard projection to make a
Publisher Dashboard projection; extract shared calculation/query behavior here
when a second projection needs the same shape.
