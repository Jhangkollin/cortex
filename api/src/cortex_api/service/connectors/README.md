# connectors domain

**PLACEHOLDER** — post-MVP.

Connectors bind external data sources (GA4, CRM, publisher feeds) to a Brand
or Publisher context. In Okis' model they are integration adapters feeding the
Discovery capability, not a persona analytics domain. Connector credentials
are encrypted at rest (application-layer Fernet, key in AWS Secrets Manager).

When implementing:
1. Define `Connector` and `ConnectorCredential` SQLModels
2. OAuth flows for each provider (GA4 first)
3. Encrypted credential storage with KMS-backed Fernet
4. Sync scheduling via Workflow / cron
5. Wire `app/api/connectors/router.py` (currently 501)

## Multi-tenancy

Connectors are bound to the active context id (`brand_id` or future
`publisher_id`). They cannot be shared across contexts at MVP/V2; cross-context
sharing is a V3 capability if real demand emerges.
