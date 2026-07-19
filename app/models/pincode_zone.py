from pydantic import BaseModel 
class Pincode_Zone(BaseModel):
    pincode: str
    warehouse_id: str