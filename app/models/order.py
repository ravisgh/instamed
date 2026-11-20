from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.ids import ObjectIdStr
from app.models.pincode_zone import PINCODE_PATTERN

OrderStatus = Literal["placed", "confirmed", "dispatched", "delivered", "cancelled"]

# Staff move an order forward one step at a time.
NEXT_STATUS: dict[str, str] = {
    "placed": "confirmed",
    "confirmed": "dispatched",
    "dispatched": "delivered",
}
CUSTOMER_CANCELLABLE = {"placed", "confirmed"}
STAFF_CANCELLABLE = {"placed", "confirmed", "dispatched"}


class OrderItemIn(BaseModel):
    medicine_id: ObjectIdStr
    quantity: int = Field(ge=1, le=100, description="Packs")


class OrderCreate(BaseModel):
    """Body for POST /orders. Stock is taken from the store that serves the pincode."""

    pincode: str = Field(pattern=PINCODE_PATTERN, examples=["560038"])
    items: list[OrderItemIn] = Field(min_length=1, max_length=50)
    prescription_id: ObjectIdStr | None = Field(
        None, description="Approved prescription; required if any item needs one"
    )

    @field_validator("items")
    @classmethod
    def _one_line_per_medicine(cls, items: list[OrderItemIn]) -> list[OrderItemIn]:
        ids = [item.medicine_id for item in items]
        if len(ids) != len(set(ids)):
            raise ValueError("each medicine may appear only once; adjust its quantity instead")
        return items


class OrderStatusUpdate(BaseModel):
    status: Literal["confirmed", "dispatched", "delivered"]


class OrderItemOut(BaseModel):
    medicine_id: str
    name: str
    pack_size: str
    quantity: int
    unit_price: float
    line_total: float


class StatusChange(BaseModel):
    status: OrderStatus
    at: datetime
    by: str


class OrderOut(BaseModel):
    id: str
    user_id: str
    store_id: str
    pincode: str
    items: list[OrderItemOut]
    total: float
    status: OrderStatus
    prescription_id: str | None = None
    created_at: datetime
    updated_at: datetime
    history: list[StatusChange]
