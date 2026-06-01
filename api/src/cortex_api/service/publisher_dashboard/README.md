# Publisher Dashboard Projection

**PLACEHOLDER** — post-MVP.

Future Publisher dashboard projection. It should reuse `service/insights/`
for shared metric snapshots, time ranges, funnel/breakdown shapes, cache keys,
and Databricks row mapping. Do not copy
`service/brand_dashboard/`; use the Brand Dashboard projection only as a
product reference for what the UI needs to display.

Likely Publisher-side metrics: traffic, answer rendering, engagement,
outbound clicks, and value created for Brands. Default breakdown dimensions
are still open and should be confirmed with Product/Data before coding
(`brand`, `article`, `campaign`, or another agreed lens).

When implementing:
1. Define the Publisher metric catalog with Product/Data
2. Extract any shared Brand behavior into `service/insights/`
3. Add the Publisher Databricks adapter over `gold_publisher_*`
4. Wire in `app/api/publisher_dashboard/router.py` (currently returns 501)
5. Add UI under `web/src/app/publisher/dashboard/` using shared dashboard primitives where possible
