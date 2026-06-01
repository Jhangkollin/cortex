# Cortex Domain Model

This is the target language from Okis' domain model. Keep code and docs aligned
with these names unless Product/Data explicitly changes the model.

## Shared Kernel

Shared kernel value objects are read-only and have no internal dependencies.
They are words every context may use but no context owns:

| VO | Meaning | Used by |
|---|---|---|
| `OrgId` | Organization scope id | Every aggregate that belongs to an org |
| `UserId` | User id | Audit, permission, and actor attribution |
| `PersonaType` | `BRAND` / `PUBLISHER` / `DEVELOPER` | Code that must decide which persona an org is acting as |
| `Money` | Money amount with currency/precision rules | Brand budget, Placement cost, future Billing |
| `Jurisdiction` | Legal region | Brand authorization scope, Publisher locale/theme, Disclosure rules |

Do not put behavior in shared kernel. If behavior needs state or ownership, it
belongs in a context below.

## Foundation And Actors

`Identity` is the foundation: target model is `Org`, `AppUser`, and
`OrgMembership`. It answers who the user is, which org they belong to, and which
persona the org is acting as. Current code still has Brand-first compatibility
tables (`brand`, `brand_membership`) and Publisher scaffolding; future identity
work should converge toward the `Org` foundation instead of adding new
per-persona membership shapes by default.

`Brand` is an actor context. It owns profile, contracts, KB sources, reference
answers, products, onboarding state, and brand-side kill switches.

`Publisher` is an actor context. It owns profile, contracts, and pointers to
versioned publisher persona assets. Keep `Publisher` as the domain/API term;
`Content Owner` is product-facing copy, not the code name.

## Capability Contexts

`Discovery` is the platform's ear. It ingests articles, extracts questions,
classifies intent, clusters topics, and tracks per-brand coverage state.

`Placement` is the decider. It checks Brand eligibility and policy, writes
append-only `PlacementDecision` / `DecisionFactor` records, and snapshots
which versions of Library assets were used.

`Agent` is the LLM gateway and task orchestrator. It composes prompts from
Library assets plus Brand state, calls LLMs, and runs quality gates.

`Library` owns versioned assets read by Agent and Placement: vertical rules,
publisher personas, disclosure text, prompt templates, and intent taxonomy.
Every asset is versioned so Placement decisions are reproducible.

## Read Model

`Insights` is a stateless Databricks read model over gold tables. It owns
persona-neutral shapes such as Metric, Funnel, Cohort, Digest, Prediction, and
Recommendation. Brand and Publisher dashboards consume Insights and apply
persona-specific shaping at the API/app boundary.
