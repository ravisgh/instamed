from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.base import UpdateModel

Role = Literal["admin", "pharmacist", "customer"]


def _normalise_email(value: str) -> str:
    return value.strip().lower()


class UserRegister(BaseModel):
    """Public sign-up body. Always creates a customer; any `role` sent is ignored."""

    email: EmailStr
    # bcrypt only uses the first 72 bytes, so longer passwords are rejected outright.
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=100)

    _email = field_validator("email")(_normalise_email)

    @field_validator("password")
    @classmethod
    def _fits_bcrypt(cls, value: str) -> str:
        if len(value.encode()) > 72:
            raise ValueError("password must be at most 72 bytes")
        return value


class UserCreate(UserRegister):
    """Admin-only body for creating staff (or any role)."""

    role: Role = "customer"


class UserUpdate(UpdateModel):
    """Admin-only PATCH: change role or (de)activate."""

    role: Role | None = None
    is_active: bool | None = None
    full_name: str | None = Field(None, min_length=1, max_length=100)


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: Role
    is_active: bool


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(description="Access token lifetime in seconds")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=200)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)

    @field_validator("new_password")
    @classmethod
    def _fits_bcrypt(cls, value: str) -> str:
        if len(value.encode()) > 72:
            raise ValueError("password must be at most 72 bytes")
        return value
