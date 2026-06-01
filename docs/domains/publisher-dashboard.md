# Publisher Dashboard Projection

Placeholder Publisher surface. It should be an API/app projection over the
shared Insights read model, not a copied Publisher Analytics bounded context.

The domain/API term is `Publisher`. Product-facing screens may use Content
Owner wording, but code, routes, JWT context, and metrics should stay aligned
with Okis' `PersonaType = PUBLISHER`.

## Implementation Rules

When the Publisher Dashboard begins:

1. Define the Publisher metric catalog with Product/Data.
2. Reuse `service/insights/` for shared metric snapshots, time ranges, cache
   keys, and Databricks row-mapping behavior.
3. Extract Brand Dashboard behavior only when the Publisher projection is a
   real second consumer of the same shape.
4. Keep Publisher-specific DTO copy, default breakdowns, and capability names
   at the projection edge.

Do not introduce `publisher_analytics` or a parallel funnel-calculation stack.
