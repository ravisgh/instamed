from datetime import date

from pydantic import BaseModel, Field

from app.models.base import UpdateModel


class MedicineBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    composition: str = Field(min_length=1, max_length=500)
    manufacturer: str = Field(min_length=1, max_length=200)
    price: float = Field(gt=0, description="MRP in INR")
    expiry_date: date = Field(description="YYYY-MM-DD")
    prescription_required: bool = False


class MedicineCreate(MedicineBase):
    """Body for POST /medicines."""


class MedicineUpdate(UpdateModel):
    """Body for PATCH /medicines/{id}: send only the fields to change."""

    name: str | None = Field(None, min_length=1, max_length=200)
    composition: str | None = Field(None, min_length=1, max_length=500)
    manufacturer: str | None = Field(None, min_length=1, max_length=200)
    price: float | None = Field(None, gt=0)
    expiry_date: date | None = None
    prescription_required: bool | None = None


class MedicineOut(MedicineBase):
    id: str
