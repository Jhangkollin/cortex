# Identity Model

Okis' target identity model is unified: `Org`, `AppUser`, and `OrgMembership`.
`OrgId` is the shared scoping key every context should FK to.

The current MVP implementation is Brand-first compatibility scaffolding. It
ships `app_user`, `brand`, and `brand_membership`; Publisher tables are
scaffolded but not migrated. Do not treat this split as the long-term domain
model.

## Bounded Contexts

| Context | Owns | Storage status |
|---|---|---|
| `identity` | Current `AppUser`; target `Org`, `AppUser`, `OrgMembership` | MVP migrated for `AppUser` only |
| `brand_identity` | Current Brand compatibility scaffold | MVP migrated |
| `publisher_identity` | Current Publisher compatibility scaffold | Scaffolded, not migrated at MVP |

A user can belong to Brand, Publisher, Developer, or future persona orgs. In
the target model, membership should be represented by `OrgMembership` plus
`PersonaType`; the current Brand/Publisher split exists because Brand onboarding
shipped first.

## MVP Schema

```sql
CREATE TABLE app_user (
  id UUID PRIMARY KEY,
  oauth_subject TEXT NOT NULL UNIQUE,
  email TEXT NOT NULL,
  display_name TEXT,
  avatar_url TEXT,
  last_login_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TYPE brandrole AS ENUM ('viewer', 'editor', 'admin');

CREATE TABLE brand (
  id UUID PRIMARY KEY,
  display_name TEXT NOT NULL,
  industry TEXT,
  domain TEXT,
  archived_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE brand_membership (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES app_user(id),
  brand_id UUID NOT NULL REFERENCES brand(id),
  role brandrole NOT NULL DEFAULT 'viewer',
  invited_by UUID REFERENCES app_user(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, brand_id)
);
```

Publisher tables are scaffolded but not migrated. Before adding more
per-persona membership tables, revisit the target `Org`/`OrgMembership`
foundation from `docs/domains/domain-model.md`.

## Scoping Rules

- `brand.id` is the current Brand scoping key and matches PHP `brand_uuid`.
- Target scoping key is `OrgId`; Brand/Publisher actor records should FK to it.
- `publisher.id` will be the current Publisher scoping key if the compatibility
  scaffold is migrated before the unified Org refactor.
- The active context comes from the JWT, not request body/query params.
- Brand routes require `active_context.kind == "brand"` and matching route id.
- Publisher routes require `active_context.kind == "publisher"` and matching route id.
- Every Databricks query and vector search filters by the active context id.

## Insights Relationship

Identity owns source-of-truth membership and authorization state. Insights is
different: Brand and Publisher dashboards are API projections over shared
read-side primitives and Databricks gold tables. Do not model Brand or
Publisher dashboard projections as separate DDD contexts.
