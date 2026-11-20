from datetime import date

from pydantic import BaseModel, Field

from app.core.ids import ObjectIdStr
from app.core.money import Rupees
from app.models.base import UpdateModel


class InventoryBase(BaseModel):
    """Stock of one medicine at one store."""

    medicine_id: ObjectIdStr
    store_id: ObjectIdStr
    quantity: int = Field(ge=0, description="Packs in stock (same unit as the medicine's MRP)")
    price: Rupees = Field(gt=0, description="Selling price per pack at this store, INR")
    earliest_expiry: date | None = Field(None, description="Expiry of the batch to sell first")
    batch_count: int = Field(1, ge=1, description="Number of batches in stock")
    location: str | None = Field(None, min_length=1, max_length=50, examples=["IPM-SR3-R02"])


class InventoryCreate(InventoryBase):
    """Body for POST /inventory. medicine_id and store_id must already exist."""


class InventoryUpdate(UpdateModel):
    """Body for PATCH /inventory/{id}. To move stock to another store, create a new row."""

    quantity: int | None = Field(None, ge=0)
    price: Rupees | None = Field(None, gt=0)
    earliest_expiry: date | None = None
    batch_count: int | None = Field(None, ge=1)
    location: str | None = Field(None, min_length=1, max_length=50)


class InventoryOut(InventoryBase):
    id: str
    price: float  # validated on input; reading older data must never fail
