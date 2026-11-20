"""Password hashing (bcrypt) and access tokens (JWT, HS256)."""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import get_settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode(), bcrypt.gensalt(rounds=get_settings().bcrypt_rounds)
    ).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:  # malformed hash or over-long password
        return False


def create_access_token(
    user_id: str, role: str, expires_in: timedelta | None = None, version: int = 0
) -> str:
    """Short-lived JWT. `version` must match the user's token_version (bumped on password
    change), so changing the password invalidates every older access token."""
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "role": role,
        "ver": version,
        "iat": now,
        "exp": now + (expires_in or timedelta(minutes=settings.access_token_minutes)),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Return the payload, or raise jwt.InvalidTokenError (bad signature, expired, ...)."""
    settings = get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["sub", "exp"]},
    )
