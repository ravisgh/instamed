from pydantic import BaseModel


class Inventory(BaseModel):
    medicine_id: str
    store_id: str
    quantity: int
    price: float