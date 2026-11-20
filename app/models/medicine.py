from typing import Literal

from pydantic import BaseModel, Field

from app.models.base import UpdateModel

# Indian drug schedules we stock. H/H1/X need a prescription; G and OTC do not.
Schedule = Literal["H", "H1", "X", "G", "OTC"]
PRESCRIPTION_SCHEDULES = {"H", "H1", "X"}

GstPercent = Literal[0, 5, 12, 18]
HSN_PATTERN = r"^\d{4,8}$"


class MedicineBase(BaseModel):
    """A catalog item (one product in one pack size). Batches and expiry live in inventory."""

    name: str = Field(min_length=1, max_length=200)
    composition: str = Field(min_length=1, max_length=1000, description="Salt(s) with strength")
    manufacturer: str = Field(min_length=1, max_length=200)
    pack_size: str = Field(min_length=1, max_length=100, examples=["15 Tablet", "100 Ml"])
    mrp: float = Field(gt=0, description="Maximum retail price per pack, INR")
    schedule: Schedule = "OTC"
    prescription_required: bool = False
    gst_percent: GstPercent
    hsn_code: str = Field(pattern=HSN_PATTERN, examples=["30049099"])


class MedicineCreate(MedicineBase):
    """Body for POST /medicines. (name, pack_size) must be unique."""


class MedicineUpdate(UpdateModel):
    """Body for PATCH /medicines/{id}: send only the fields to change."""

    name: str | None = Field(None, min_length=1, max_length=200)
    composition: str | None = Field(None, min_length=1, max_length=1000)
    manufacturer: str | None = Field(None, min_length=1, max_length=200)
    pack_size: str | None = Field(None, min_length=1, max_length=100)
    mrp: float | None = Field(None, gt=0)
    schedule: Schedule | None = None
    prescription_required: bool | None = None
    gst_percent: GstPercent | None = None
    hsn_code: str | None = Field(None, pattern=HSN_PATTERN)


class MedicineOut(MedicineBase):
    id: str
