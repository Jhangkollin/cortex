# Brand Dashboard Projection

The flagship Brand Dashboard projection. It serves 4 KPI cards and a
per-publisher breakdown for the active `BrandTenantCtx`.

This is **not** a standalone DDD bounded context. It is the current Brand
Dashboard API adapter over the Insights read model. Shared read-model behavior
belongs in `service/insights/`: time ranges, metric snapshots, and generic
metric-set typing. Keep this package focused on Brand-specific metric catalog
choices, Brand auth/capability wiring, per-publisher breakdown naming, and
Brand DTO mapping.

## Metrics

| Key | Chinese | Source |
|---|---|---|
| `answer_produced` | Answer page 生產次數 | `aigc_metrics.content_metrics` (filtered by active `brand_id`) |
| `answer_views` | Answer page 觀看次數 | `aigc_metrics.view_metrics` |
| `llm_citations` | LLM 引用 Answer 次數 | `aigc_metrics.llm_metrics` |
| `brand_clicks` | 品牌 link 點擊次數 | `events_silver.click_brand_slug` |

Each metric on the gold table is **three columns**:
- `<metric>` — current period total (the big number)
- `delta_pct_<metric>` — % change vs previous same-length period (the badge)
- `points_<metric>` — daily values (the sparkline)

## Endpoints

- `GET /v1/brand/{brand_id}/analytics/metrics?range=30d` — 4 KPIs
- `GET /v1/brand/{brand_id}/analytics/metrics/by-publisher?metric=&range=&limit=20&offset=0` — drill-down

## Gold tables (consumed; owned by data-eng repo)

- `aigc_metrics.gold_brand_answer_metrics` — one row per `(brand_uuid, range_label)` or the agreed Brand scoping column
- `aigc_metrics.gold_brand_publisher_breakdown` — one row per `(brand_uuid, publisher_id, range_label)` or the agreed Brand scoping column

Both filter by the active `brand_id` from `BrandTenantCtx`. Do not trust
client-supplied scoping fields.

## Cache

Redis 5min TTL, key `(brand_id, view, range)` for top-level and
`(brand_id, "by-publisher", metric, range, page)` for breakdown. Keep the
convention aligned with `service/insights/` before adding publisher-side
insights.

## Slicing

This projection ships in feature slices (see `cortex-mvp-plan-zh.md`):
- Slice 1 — first metric (`answer_produced`) end-to-end
- Slice 2 — sparkline + remaining 3 metrics
- Slice 3 — time range filter
- Slice 4 — publisher breakdown drill-down
- Slice 5 — delta + empty/loading/error states

When a second persona projection needs the same behavior, extract the common
piece into `service/insights/` before implementing the persona adapter. Do not
turn this package into a Brand-owned analytics domain.
