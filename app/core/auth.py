"""Auth dependencies: who is calling, and are they allowed?"""

from typing import Annotated, Any

import jwt
from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token
from app.repositories import Repos

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

_unauthorized = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    repos: Repos, token: Annotated[str, Depends(oauth2_scheme)]
) -> dict[str, Any]:
    """The active user the bearer token belongs to, or 401."""
    try:
        payload = decode_access_token(token)
    except jwt.InvalidTokenError:
        raise _unauthorized from None
    user_id = payload.get("sub", "")
    if not ObjectId.is_valid(user_id):
        raise _unauthorized
    user = await repos.users.find_one({"_id": ObjectId(user_id)})
    if user is None or not user.get("is_active", False):
        raise _unauthorized
    if payload.get("ver", 0) != user.get("token_version", 0):
        raise _unauthorized  # issued before the last password change
    return user


CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]


def require_roles(*roles: str):
    """Dependency factory: 403 unless the current user has one of `roles`."""

    async def checker(user: CurrentUser) -> dict[str, Any]:
        if user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )
        return user

    return checker


# Ready-made guards for routes.
AdminOnly = Depends(require_roles("admin"))
StaffOnly = Depends(require_roles("admin", "pharmacist"))
