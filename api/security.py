"""
HomeGuard Security Module
=========================
JWT authentication, password hashing, and OAuth2 configuration.

Security Parameters (from environment):
- SECRET_KEY: JWT signing key (min 32 chars)
- ALGORITHM: JWT algorithm (default: HS256)
- ACCESS_TOKEN_EXPIRE_MINUTES: Token TTL (default: 30 min)

CP-10 Compliance:
- Tokens stored in memory only (no localStorage persistence)
- Short-lived access tokens (30 min default)
- Refresh token rotation on each use
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-at-least-32-chars-long")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing - bcrypt with automatic salt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 password flow - tells clients how to get tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ---------------------------------------------------------------------------
# Password Hashing
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)

# ---------------------------------------------------------------------------
# JWT Token Operations
# ---------------------------------------------------------------------------


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload claims (must include 'sub' as user identifier).
        expires_delta: Custom expiry; defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Signed JWT token string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    """
    Create a JWT refresh token (longer-lived, type-tagged).

    Refresh tokens live 7 days and can only be used to obtain new access tokens.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: The JWT string to decode.
        expected_type: Expected token type ("access" or "refresh").

    Returns:
        Decoded payload dictionary.

    Raises:
        HTTPException: If token is invalid, expired, or wrong type.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Expected {expected_type} token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload

# ---------------------------------------------------------------------------
# FastAPI Dependencies
# ---------------------------------------------------------------------------


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> str:
    """
    Extract the current user ID from the JWT access token.

    Returns the `sub` claim (user UUID) as a string.
    Raises 401 if token is invalid or expired.

    Usage:
        @router.get("/me")
        async def me(current_user: str = Depends(get_current_user)):
            return {"user_id": current_user}
    """
    payload = decode_token(token, expected_type="access")
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing sub claim",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


async def get_optional_user(
    token: str | None = Depends(oauth2_scheme),
) -> str | None:
    """
    Optionally extract the current user ID.

    Returns None if no token is provided (for public endpoints that enhance
    response when authenticated). Does NOT raise 401 for missing/invalid tokens.
    """
    if token is None:
        return None
    try:
        payload = decode_token(token, expected_type="access")
        return payload.get("sub")
    except HTTPException:
        return None