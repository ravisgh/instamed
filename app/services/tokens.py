"""Session tokens: short-lived JWT access tokens + rotating opaque refresh tokens.

Refresh tokens are random strings; only their SHA-256 hash is stored. Each refresh
replaces the token with a new one in the same *family*. If an already-used token shows
up again, someone copied it, so the whole family is revoked and both parties must log
in again (refresh-token reuse detection).
"""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import PasswordChange, Token
from app.repositories import Repositories

log = get_logger("tokens")

_invalid_refresh = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired refresh token",
    headers={"WWW-Authenticate": "Bearer"},
)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def issue(repos: Repositories, user: dict[str, Any], family_id: str | None = None) -> Token:
    settings = get_settings()
    refresh_token = secrets.token_urlsafe(48)
    now = datetime.now(UTC)
    await repos.refresh_tokens.collection.insert_one(
        {
            "token_hash": _hash(refresh_token),
            "user_id": user["id"],
            "family_id": family_id or uuid.uuid4().hex,
            "created_at": now,
            "expires_at": now + timedelta(days=settings.refresh_token_days),
            "revoked_at": None,
        }
    )
    access = create_access_token(user["id"], user["role"], version=user.get("token_version", 0))
    return Token(
        access_token=access,
        refresh_token=refresh_token,
        expires_in=settings.access_token_minutes * 60,
    )


async def _revoke_family(repos: Repositories, family_id: str) -> None:
    await repos.refresh_tokens.collection.update_many(
        {"family_id": family_id, "revoked_at": None}, {"$set": {"revoked_at": datetime.now(UTC)}}
    )


async def rotate(repos: Repositories, refresh_token: str) -> Token:
    now = datetime.now(UTC)
    # Atomically claim the token: only one request can turn revoked_at from None to now.
    record = await repos.refresh_tokens.collection.find_one_and_update(
        {"token_hash": _hash(refresh_token), "revoked_at": None, "expires_at": {"$gt": now}},
        {"$set": {"revoked_at": now}},
    )
    if record is None:
        used = await repos.refresh_tokens.collection.find_one(
            {"token_hash": _hash(refresh_token), "revoked_at": {"$ne": None}}
        )
        if used is not None:
            log.warning(
                "Refresh token reuse detected; revoking family for user %s", used["user_id"]
            )
            await _revoke_family(repos, used["family_id"])
        raise _invalid_refresh

    user = await repos.users.find_one({"_id": ObjectId(record["user_id"])})
    if user is None or not user.get("is_active", False):
        await _revoke_family(repos, record["family_id"])
        raise _invalid_refresh
    return await issue(repos, user, family_id=record["family_id"])


async def logout(repos: Repositories, refresh_token: str) -> None:
    record = await repos.refresh_tokens.collection.find_one({"token_hash": _hash(refresh_token)})
    if record is not None:
        await _revoke_family(repos, record["family_id"])


async def change_password(repos: Repositories, user: dict[str, Any], body: PasswordChange) -> None:
    if not verify_password(body.current_password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect"
        )
    await repos.users.collection.update_one(
        {"_id": ObjectId(user["id"])},
        {
            "$set": {"password_hash": hash_password(body.new_password)},
            "$inc": {"token_version": 1},  # every older access token stops working
        },
    )
    await repos.refresh_tokens.collection.update_many(
        {"user_id": user["id"], "revoked_at": None}, {"$set": {"revoked_at": datetime.now(UTC)}}
    )
    log.info("Password changed for user %s; sessions revoked", user["id"])
