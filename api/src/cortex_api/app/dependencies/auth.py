"""Authentication Depends — decode JWT, produce AuthedUser.

Mirrors agent-will-smith's auth pattern but at the dep layer (not middleware).
Reads the bearer token, verifies signature, returns a frozen value object.

Public routes (system) skip this dep entirely.
"""

from __future__ import annotations

from typing import Annotated, cast
from uuid import UUID

import jwt
import structlog
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Header

from cortex_api.core.config.auth_config import AuthConfig
from cortex_api.core.container import Container as CoreContainer
from cortex_api.core.exceptions import UnauthorizedError
from cortex_api.service.identity.container import Container as IdentityContainer
from cortex_api.service.identity.model.app_user import AppUser
from cortex_api.service.identity.model.authed_user import AuthedUser
from cortex_api.service.identity.service import UserService

_logger = structlog.get_logger(__name__)


@inject
def authenticated_user(
    authorization: Annotated[str, Header(alias="Authorization")] = "",
    auth_config: AuthConfig = Depends(Provide[CoreContainer.auth_config]),
) -> AuthedUser:
    """Decode the bearer JWT and return AuthedUser.

    Raises UnauthorizedError on any signature / claim verification failure.
    The full claim dict is attached as `raw_claims` for downstream deps
    (active_brand, active_publisher) to read context-specific fields.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("missing or malformed Authorization header")

    token = authorization[len("Bearer ") :].strip()

    try:
        claims = jwt.decode(
            token,
            auth_config.nextauth_secret,
            algorithms=[auth_config.jwt_algorithm],
            audience=auth_config.jwt_audience,
            issuer=auth_config.jwt_issuer,
        )
    except jwt.PyJWTError as e:
        raise UnauthorizedError(f"JWT verification failed: {e}") from e

    try:
        user_id = UUID(cast("str", claims["sub"]))
        email = cast("str", claims["email"])
    except (KeyError, ValueError) as e:
        raise UnauthorizedError(f"JWT missing required claim: {e}") from e

    return AuthedUser(
        user_id=user_id,
        email=email,
        display_name=claims.get("display_name"),
        raw_claims=claims,
    )


@inject
async def current_app_user(
    user: AuthedUser = Depends(authenticated_user),
    user_service: UserService = Depends(Provide[IdentityContainer.service]),
) -> AppUser:
    """Resolve the calling JWT to an AppUser row.

    Dispatches on the `token_kind` JWT claim (set by cortex-web's token
    signers):

    - ``"bootstrap"`` — JWT carries Google ``oauth_subject``; upsert AppUser
      by it (creates the row on first-ever sign-in, refreshes on subsequent
      bootstrap calls).
    - ``"session"`` — JWT ``sub`` IS the app_user UUID (resolved on a prior
      bootstrap); fetch by ``user_id``.
    - missing / unknown — 401. Catches NextAuth misconfiguration (e.g.,
      legacy session cookie minted before this contract was tightened) at
      the boundary instead of silently hitting the wrong branch.

    See ``docs/auth.md`` § "Bootstrap vs session token shapes".
    """
    token_kind = user.raw_claims.get("token_kind")
    if token_kind == "bootstrap":
        oauth_subject = user.raw_claims.get("oauth_subject")
        if not oauth_subject:
            raise UnauthorizedError("bootstrap token missing oauth_subject claim")
        return await user_service.recognize_user(
            oauth_subject=str(oauth_subject),
            email=user.email,
            display_name=user.display_name,
        )
    if token_kind == "session":
        return await user_service.get_user(user.user_id)
    raise UnauthorizedError(f"missing or unknown token_kind claim: {token_kind!r} (expected 'bootstrap' or 'session')")
