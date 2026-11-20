from pydantic import BaseModel


class Medicine(BaseModel):
    name: str
    composition: str
    manufacturer: str
    price: float
    expiry_date: str
    prescription_required: bool = False