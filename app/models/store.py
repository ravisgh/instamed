from pydantic import BaseModel
class Store(BaseModel):
    name: str
    latitude: float
    longitude: float
    contact_number: str
    email: str
    opening_hours: str