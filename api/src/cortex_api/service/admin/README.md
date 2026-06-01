# admin domain

**PLACEHOLDER** — future. This domain replaces aigc-mvp's PHP admin once Cortex is mature enough to host all internal management surfaces.

Eventually owns:
- Org provisioning (create / archive / rename)
- User management (invite, revoke, role changes)
- Subscription state toggling
- Connector credential rotation
- Analytical observability surfaces (refresh job status, attribution coverage)

Until then, internal operations stay in the PHP admin (aigc-mvp). Do not start work here without explicit migration plan.

When implementing:
1. Define which admin surfaces are migrating from PHP first
2. Coordinate with PHP for cutover
3. Wire `app/api/admin/router.py` (currently 501)
4. UI under `web/src/app/admin/`
