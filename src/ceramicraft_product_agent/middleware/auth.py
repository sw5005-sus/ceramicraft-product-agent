"""Authentication middleware.

Supports two auth modes:
1. JWT Bearer token (Authorization header) — for direct API calls
2. Traefik X-Original-User-ID header — for requests via cluster ingress
   (Traefik's zitadel-auth middleware verifies the session and injects the user ID)
"""

from __future__ import annotations

import os
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ceramicraft_product_agent.utils.logger import get_logger

logger = get_logger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)


def _get_jwt_secret() -> str:
    secret = os.environ.get("JWT_SECRET", "")
    return secret


def decode_token(token: str) -> dict[str, Any]:
    secret = _get_jwt_secret()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication not configured.",
        )
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        )


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict[str, Any]:
    """Extract user identity from either JWT or Traefik header.

    Priority:
    1. X-Original-User-ID header (set by Traefik zitadel-auth middleware)
    2. Authorization: Bearer <JWT> header (direct API calls)
    """
    traefik_user_id = request.headers.get("X-Original-User-ID")
    if traefik_user_id:
        logger.info("Authenticated via Traefik header: user_id=%s", traefik_user_id)
        return {
            "user_id": traefik_user_id,
            "role": "merchant_admin",
        }

    if credentials is not None:
        return decode_token(credentials.credentials)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authorization header.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_roles(*allowed_roles: str):
    async def _check_roles(
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        user_role = user.get("role", "")
        if user_role not in allowed_roles:
            logger.warning(
                "Access denied for user %s with role %s (required: %s)",
                user.get("user_id", "unknown"),
                user_role,
                allowed_roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}",
            )
        return user

    return _check_roles
