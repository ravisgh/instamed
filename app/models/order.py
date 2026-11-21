from pydantic import BaseModel
from typing import List

class OrderItem(BaseModel):
    medicine_id: str
    quantity: int

class Order(BaseModel):
    customer_name: str
    customer_phone: str
    address: str
    warehouse_id: str
    items: List[OrderItem]
    status: str = "Pending" 
    total_price: float 
