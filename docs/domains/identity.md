# Identity Foundation

Identity is the foundation for everything. Okis' target model is `Org`,
`AppUser`, and `OrgMembership`; the current MVP implementation is Brand-first
compatibility scaffolding. See `api/src/cortex_api/service/identity/README.md`
for the live README.

## Why this is the first domain to land

- Auth dependencies can't resolve an `AppUser` without `app_user` rows
- Brand context resolution depends on `brand` + `brand_membership`
- Every analytical query depends on the JWT `active_context` matching the route id

Until identity is live, protected endpoints fail at the auth/context boundary
with 401 / 403 / 400 errors.

## Slice plan

1. **Schema** — Alembic migration creating `app_user`, `brand`, `brand_membership`, and `brandrole`
2. **Repos** — implement user + brand membership persistence
3. **Services** — `UserService.recognize_user`, `BrandIdentityService.enter_brand`, membership listing
4. **Dependencies** — `authenticated_user`, `current_app_user`, `active_brand`, capability gates
5. **Endpoints** — `GET /v1/auth/me`, `POST /v1/auth/resolve-context`, `POST /v1/brand`
6. **Frontend** — read memberships, choose active context, bake it into the Cortex API JWT

After this, the Brand Dashboard API projection Slice 1 can land on top of the
shared Insights read model.

## Key implementation notes

- Use `oauth_subject` from Google `sub` claim as the user identity, not email
- Current Brand scoping uses `brand.id`, which matches PHP `brand_uuid`; target
  scoping is `OrgId`
- Capability checks are zero-DB on protected routes; role/capability values are baked into `active_context`
- All queries must scope by the active context id; never trust client-supplied tenant context
