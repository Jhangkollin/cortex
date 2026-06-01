# knowledge_base domain

**PLACEHOLDER** — post-MVP.

Vector search placeholder over duplicated 天下 KB and future per-context assets.
Okis' target model calls this versioned asset area `Library`: vertical rules,
publisher personas, disclosures, prompt templates, and intent taxonomy. Do not
grow this package into a permanent standalone Knowledge Base bounded context.
When Library lands, versioned assets should move behind that vocabulary.

Uses `infra/vector_search_client.py`. Always filters by namespace derived from
the active Brand or Publisher context.

When implementing:
1. Define KB ingestion / chunking pipeline (data-eng repo)
2. Build `KnowledgeBaseService` with semantic search + filter by active context
3. Wire in `app/api/knowledge_base/router.py` (currently returns 501)
4. Add UI under `web/src/app/knowledge/`

## Multi-tenancy

Namespace from the active context is the partition key. Two contexts sharing
天下 source content (one brand, one publisher) get different namespaces and
different filtered views.
