# Domains

Cortex domain vocabulary and current implementation surfaces. Some entries are
target domain language from Okis' model and do not yet have a one-to-one
`service/<name>/` package.

| Surface | Status | Doc |
|---|---|---|
| shared kernel | target | [domain-model.md](domain-model.md) |
| identity foundation | MVP Brand-first; target unified Org/AppUser/OrgMembership | [identity.md](identity.md) |
| brand / publisher actors | Brand MVP, Publisher scaffolded | [domain-model.md](domain-model.md) |
| discovery / placement / agent / library | target capability contexts | [domain-model.md](domain-model.md) |
| insights read model | MVP shared primitives | [insights.md](insights.md) |
| Brand Dashboard API projection | MVP | [brand-dashboard.md](brand-dashboard.md) |
| Publisher Dashboard API projection | placeholder | [publisher-dashboard.md](publisher-dashboard.md) |
| knowledge_base | placeholder | (superseded by Library when versioned assets land) |
| connectors | placeholder | (integration adapters feeding Discovery) |
| admin | placeholder | (TBD when work begins) |

Write-side domains follow the agent-will-smith pattern: `service.py`,
`config.py`, `container.py`, `model/`, `repo/`. Insights is different:
persona-neutral read-model primitives live in `service/insights/`, while
dashboard route modules shape them for Brand or Publisher.
