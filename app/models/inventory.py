from pydantic import BaseModel, Field

from app.core.ids import ObjectIdStr
from app.models.base import UpdateModel


class InventoryBase(BaseModel):
    medicine_id: ObjectIdStr
    store_id: ObjectIdStr
    quantity: int = Field(ge=0, description="Units in stock")
    price: float = Field(gt=0, description="Selling price at this store, INR")


class InventoryCreate(InventoryBase):
    """Body for POST /inventory. medicine_id and store_id must already exist."""


class InventoryUpdate(UpdateModel):
    """Body for PATCH /inventory/{id}. To move stock to another store, create a new row."""

    quantity: int | None = Field(None, ge=0)
    price: float | None = Field(None, gt=0)


class InventoryOut(InventoryBase):
    id: str
