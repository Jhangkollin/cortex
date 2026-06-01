"""FastAPI Depends factories — auth, tenant, capability gates.

Replaces the auth_middleware and org_context_middleware. Per the wiki §2.2,
use cases consume `TenantCtx` as explicit parameters; framework state never
leaks into the application layer.
"""
