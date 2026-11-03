# ============================================================
# Standard Library
# ============================================================

from datetime import datetime, timedelta, timezone
from uuid import UUID

# ============================================================
# Third Party
# ============================================================

from jose import JWTError, jwt
from typing import Any

# FastAPI exceptions/status
from fastapi import HTTPException, status

# ============================================================
# Local Imports
# ============================================================

from app.core.config import settings

# ============================================================
# Constants
# ============================================================

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

# ============================================================
# Public Functions
# ============================================================


def create_access_token(data: dict[str, Any]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode = data.copy()
    
    to_encode.update(
        {
            "type": ACCESS_TOKEN_TYPE,
            "exp": expire,
        }
    )

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_refresh_token(
    user_id: UUID,
) -> str:
    """
    Create a JWT Refresh Token.

    Args:
        user_id: Authenticated user's UUID.

    Returns:
        Encoded JWT refresh token.
    """

    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    payload = {
        "sub": str(user_id),
        "type": REFRESH_TOKEN_TYPE,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_token(
    token: str,
) -> dict:
    """
    Decode a JWT token.

    Args:
        token: JWT token.

    Returns:
        Decoded payload.

    Raises:
        JWTError: If token is invalid or expired.
    """

    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )


# ============================================================
# Verify Access Token
# ============================================================

def verify_access_token(
    token: str,
) -> dict:
    """
        Verify an access token and return its payload.

        Args:
            token: JWT access token.

        Returns:
            Decoded JWT payload.

        Raises:
            HTTPException:
                If the token is invalid,
                expired,
                or not an access token.
    """

    try:

        payload = decode_token(token)

        if payload.get("type") != ACCESS_TOKEN_TYPE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token.",
            )

        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )