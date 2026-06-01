# brand_identity compatibility scaffold

Current Brand-first write side for tenant login/onboarding. This exists because
Brand shipped before the unified `Org` foundation. Do not use it as a template
for new persona domains.

Owns:

- `Brand` (SQLModel, Active Record)
- `BrandMembership` (N-to-N AppUser ↔ Brand)
- `BrandRole` (viewer | editor | admin)
- `BrandCapability` (enum, brand-only capabilities)
- `BrandTenantCtx` (frozen value object — the keystone passed through every brand route)

## Invariants

- `Brand.id` is the current Brand scoping key. Same value used as `brand_uuid` in Databricks WHERE clauses.
- Target scoping language is `OrgId`; future refactors should make Brand an
  actor record scoped by Org.
- Membership is verified at login (when JWT is issued); capabilities pre-resolved and baked into JWT claims.
- Hot-path requests never hit DB for permission — `BrandTenantCtx` carries everything.
- `BrandRole` and `BrandCapability` are **strictly brand-side**. No cross-contamination with publisher types.

## Use cases (BrandIdentityService)

- `enter_brand(user, brand_id)` — verify membership at login / context switch
- `recognize_membership(user_id, brand_id)` — fetch a single membership row
- `list_user_brands(user_id)` — list every brand the user can act on
- `grant_brand_membership(actor, brand_id, user_id, role)` — admin op
- `revoke_brand_membership(actor, membership_id)` — admin op

## Capability matrix

See `policy/brand_capability_policy.py`. Single source of truth — frontend
reads resolved list from JWT, backend re-validates per route via
`requires_brand_capability(...)` dep.
