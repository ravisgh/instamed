from pydantic import BaseModel, EmailStr, Field

from app.models.base import UpdateModel

# Indian mobile/landline, optional +country code: 10-13 digits.
PHONE_PATTERN = r"^\+?[0-9]{10,13}$"


class StoreBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    contact_number: str = Field(pattern=PHONE_PATTERN, examples=["+919876543210"])
    email: EmailStr
    opening_hours: str = Field(min_length=1, max_length=100, examples=["08:00-22:00"])


class StoreCreate(StoreBase):
    """Body for POST /stores."""


class StoreUpdate(UpdateModel):
    """Body for PATCH /stores/{id}: send only the fields to change."""

    name: str | None = Field(None, min_length=1, max_length=200)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    contact_number: str | None = Field(None, pattern=PHONE_PATTERN)
    email: EmailStr | None = None
    opening_hours: str | None = Field(None, min_length=1, max_length=100)


class StoreOut(StoreBase):
    id: str
