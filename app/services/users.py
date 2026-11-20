from typing import Any

from fastapi import HTTPException, status

from app.core.metrics import LOGIN_FAILURES
from app.core.security import hash_password, verify_password
from app.models.user import UserCreate, UserRegister
from app.repositories import Repositories

_bad_login = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect email or password",
    headers={"WWW-Authenticate": "Bearer"},
)


async def create_user(
    repos: Repositories, body: UserRegister, role: str = "customer"
) -> dict[str, Any]:
    if isinstance(body, UserCreate):
        role = body.role
    return await repos.users.insert(
        {
            "email": body.email,
            "full_name": body.full_name,
            "role": role,
            "is_active": True,
            "password_hash": hash_password(body.password),
        }
    )


async def authenticate(repos: Repositories, email: str, password: str) -> dict[str, Any]:
    """The active user with these credentials, or 401 (same message for every failure)."""
    user = await repos.users.find_one({"email": email.strip().lower()})
    if user is None or not verify_password(password, user["password_hash"]):
        LOGIN_FAILURES.inc()
        raise _bad_login
    if not user.get("is_active", False):
        raise _bad_login
    return user
