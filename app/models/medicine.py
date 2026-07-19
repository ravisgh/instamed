from pydantic import BaseModel, Field
from typing import Optional

class Medicine(BaseModel):
    name: str
    composition: str
    manufacturer: str
    price: float
    expiry_date: str
    prescription_required: bool = False