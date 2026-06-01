# api-client

This directory holds the **auto-generated** TypeScript client for `cortex-api`.

**Do not edit `generated/` by hand.** Run:

```bash
npm run generate-client
```

This runs `@hey-api/openapi-ts` against `../api/openapi.json` and emits typed SDK + TanStack Query options into `generated/`. Commit the regenerated files alongside any backend DTO changes.

## Usage in components

```tsx
"use client";
import { useQuery } from "@tanstack/react-query";
import { getMetricsOptions } from "@/lib/api-client/generated";

export function KpiGrid({ range }: { range: "30d" | "7d" }) {
  const { data } = useQuery(getMetricsOptions({ query: { range } }));
  return <div>{data?.metrics.answer_views.value}</div>;
}
```

## When to regenerate

- Any change to `api/src/cortex_api/app/api/*/dto.py`
- Any router signature change (params, response types)
- Adding a new endpoint
