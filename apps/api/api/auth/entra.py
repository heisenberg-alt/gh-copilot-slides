"""
Microsoft Entra ID (Azure AD) authentication.

Validates JWT tokens issued by Entra ID and extracts user information.
"""

import logging
from typing import Optional
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from jose import jwt, JWTError

from ..config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

# JWKS client for token validation
_jwks_client: Optional[httpx.Client] = None
_jwks_cache: dict = {}


@dataclass
class User:
    """Authenticated user information."""

    id: str  # Object ID (oid claim)
    email: str
    name: str
    roles: list[str]


def get_jwks_uri() -> str:
    """Get the JWKS URI for the configured tenant."""
    return f"https://login.microsoftonline.com/{settings.azure_tenant_id}/discovery/v2.0/keys"


def get_issuer() -> str:
    """Get the expected token issuer."""
    return f"https://login.microsoftonline.com/{settings.azure_tenant_id}/v2.0"


async def get_signing_key(token: str) -> dict:
    """
    Get the signing key for a token from Entra ID JWKS endpoint.

    Caches keys to avoid repeated network calls.
    """
    global _jwks_cache

    # Decode header to get key ID
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")

    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing key ID",
        )

    # Check cache
    if kid in _jwks_cache:
        return _jwks_cache[kid]

    # Fetch JWKS
    async with httpx.AsyncClient() as client:
        response = await client.get(get_jwks_uri())
        response.raise_for_status()
        jwks = response.json()

    # Find matching key
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            _jwks_cache[kid] = key
            return key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unable to find signing key",
    )


async def validate_token(token: str) -> dict:
    """
    Validate a JWT token from Entra ID.

    Returns the decoded claims if valid.
    """
    try:
        signing_key = await get_signing_key(token)

        # Decode and validate token
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=settings.azure_client_id,
            issuer=get_issuer(),
            options={
                "verify_aud": True,
                "verify_iss": True,
                "verify_exp": True,
            },
        )

        return claims

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> User:
    """
    Dependency to get the current authenticated user.

    Validates the Bearer token and returns user information.
    In DEBUG mode with no auth configured, returns a mock user (non-admin).
    """
    # Development mode bypass - only when DEBUG=true AND no auth configured
    if settings.debug and (not settings.azure_tenant_id or not settings.azure_client_id):
        logger.warning("AUTH BYPASS: Running in debug mode without Azure AD configuration")
        return User(
            id="dev-user-001",
            email="developer@localhost",
            name="Developer (Debug Mode)",
            roles=["User"],  # Non-admin by default for safety
        )

    # Production mode - require proper authentication
    if not settings.azure_tenant_id or not settings.azure_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not configured. Set AZURE_TENANT_ID and AZURE_CLIENT_ID.",
        )

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate token
    claims = await validate_token(credentials.credentials)

    # Extract user info
    return User(
        id=claims.get("oid", claims.get("sub", "")),
        email=claims.get("preferred_username", claims.get("email", "")),
        name=claims.get("name", ""),
        roles=claims.get("roles", []),
    )


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Dependency that requires admin role."""
    if "Admin" not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
