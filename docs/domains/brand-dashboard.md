# Brand Dashboard Projection

Flagship Brand surface: 4 KPIs + per-publisher breakdown for an active
`BrandTenantCtx`. See
`api/src/cortex_api/service/brand_dashboard/README.md` for the live
README.

This is a persona projection over the shared insights read side, not a DDD
bounded context to copy for other personas. Brand-specific metric catalogs,
breakdown defaults, and route DTO wording live here; reusable metric/time-range
primitives live in `service/insights/`.

## Slice plan

| Slice | Scope | DoD |
|---|---|---|
| 1 | First metric (`answer_produced`) end-to-end (Databricks → API → UI) | One real number rendered on `/brand/dashboard` |
| 2 | Sparkline + remaining 3 metrics (`answer_views`, `llm_citations`, `brand_clicks`) | 4 KPI cards with sparklines |
| 3 | Time range filter (7d / 30d / 90d / mtd) | Switching range updates all 4 cards |
| 4 | Publisher breakdown — click KPI to expand | `<PublisherBreakdownTable>` rendering rows for the active metric |
| 5 | Delta % badges + empty / loading / error states | All states tested with synthetic data |
| 6 | Polish + demo prep | Demo-ready, screenshots, walk-through video |

See `../../aigc_coordinator/cortex-mvp-plan-zh.md` for the full MVP plan with feature slice estimates.

## Gold tables (consumed; owned in data-eng repo)

```
aigc_metrics.gold_brand_answer_metrics
  PK: (brand_uuid, range_label) or agreed Brand scoping column
  Columns: <metric>, delta_pct_<metric>, points_<metric>, refreshed_at

aigc_metrics.gold_brand_publisher_breakdown
  PK: (brand_uuid, publisher_id, range_label) or agreed Brand scoping column
  Same metric column shape, plus publisher_name
```

Both refreshed every 30 min by a Databricks Workflow living in the data-eng repo.

## Cache strategy

| Layer | Key | TTL |
|---|---|---|
| Redis | `(brand_id, "metrics", range)` | 5 min |
| Redis | `(brand_id, "by-publisher", metric, range, page)` | 5 min |
| TanStack Query | `["brand-metrics", brand_id, range]` | 5 min staleTime |
