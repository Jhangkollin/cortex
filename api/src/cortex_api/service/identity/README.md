# Identity Foundation

Foundation for everything else.

Target model from Okis' domain map:

- `Org` — tenant scope, with a `PersonaType` (`BRAND`, `PUBLISHER`, `DEVELOPER`)
- `AppUser` — one row per OAuth subject
- `OrgMembership` — AppUser membership, role, and capability source

Current MVP implementation owns:

- `AppUser` (one row per OAuth subject)

## Invariants

- Current code does not own memberships yet. Brand memberships live in
  `brand_identity`; Publisher memberships are scaffolded in
  `publisher_identity`.
- Future identity work should converge on `Org` / `OrgMembership` instead of
  adding more per-persona membership shapes by default.
- `oauth_subject` from Google `sub` is the authoritative user identity.
- A single `AppUser` can hold memberships in Brand, Publisher, Developer, or
  future persona orgs.

## API surface

- `GET /v1/users/me` — return the calling user
- `POST /v1/auth/resolve-context` — verify membership and return role/capabilities for NextAuth to bake into a JWT

## Relationship to auth

- `app/dependencies/auth.py` decodes the JWT and returns `AuthedUser`.
- `app/dependencies/brand.py` and `app/dependencies/publisher.py` validate
  `active_context` and return tenant context value objects.
- Brand and Publisher capability dependencies re-validate backend permissions
  for every protected route. Frontend permissions are UX only.
