"""JWT authentication middleware.

Compatible with ceramicraft-user-mservice JWT tokens.
Reads JWT_SECRET from environment and verifies Bearer tokens
in the Authorization header.
"""

from __future__ import annotations

import os
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ceramicraft_product_agent.utils.logger import get_logger

logger = get_logger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)


def _get_jwt_secret() -> str:
    """Return the JWT secret from environment."""
    secret = os.environ.get("JWT_SECRET", "")
    if not secret:
        logger.warning("JWT_SECRET not set — authentication will reject all requests.")
    return secret


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT token.

    Returns the decoded payload dict.
    Raises HTTPException on invalid/expired tokens.
    """
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
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict[str, Any]:
    """FastAPI dependency that extracts and verifies the JWT token.

    Returns the decoded user payload containing user_id, roles, etc.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials)


def require_roles(*allowed_roles: str):
    """Return a FastAPI dependency that enforces role-based access control.

    Usage:
        @router.post("/endpoint")
        async def handler(user: dict = Depends(require_roles("merchant_admin", "product_editor"))):
            ...
    """

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
