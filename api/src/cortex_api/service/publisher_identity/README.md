# publisher_identity compatibility scaffold

Scaffold for publisher-side login/onboarding. It mirrors `brand_identity` today
only as a compatibility bridge; Publisher tables are not migrated at MVP. Do
not use it as a template for new persona domains.

Owns:

- `Publisher` (SQLModel, Active Record)
- `PublisherMembership` (N-to-N AppUser ↔ Publisher)
- `PublisherRole` (viewer | editor | admin)
- `PublisherCapability` (enum, publisher-only capabilities)
- `PublisherTenantCtx` (frozen value object — keystone for every publisher route)

## Invariants

- `Publisher.id` is the current Publisher scoping key. Same value as `publisher_uuid`
  in Databricks WHERE clauses against publisher-side gold tables.
- Target scoping language is `OrgId`; future refactors should make Publisher an
  actor record scoped by Org.
- Membership verified at login; capabilities baked into JWT claims.
- Hot path never hits DB for permission.
- `PublisherRole` and `PublisherCapability` are **strictly publisher-side**.
  No cross-contamination with brand types — type system enforces.

## Use cases (PublisherIdentityService)

- `enter_publisher(user, publisher_id)` — verify membership at login / context switch
- `list_user_publishers(user_id)` — list every publisher the user can act on
- `grant_publisher_membership(actor, publisher_id, user_id, role)` — admin op
- `revoke_publisher_membership(actor, membership_id)` — admin op

## Capability matrix

See `policy/publisher_capability_policy.py`. Single source of truth — frontend
reads resolved list from JWT, backend re-validates per route via
`requires_publisher_capability(...)` dep.
