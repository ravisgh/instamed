from pydantic import BaseModel, Field

from app.core.ids import ObjectIdStr
from app.models.base import UpdateModel

# Indian PIN code: 6 digits, first digit 1-9.
PINCODE_PATTERN = r"^[1-9][0-9]{5}$"


class PincodeZoneBase(BaseModel):
    pincode: str = Field(pattern=PINCODE_PATTERN, examples=["560038"])
    warehouse_id: ObjectIdStr = Field(description="Id of the store that serves this pincode")


class PincodeZoneCreate(PincodeZoneBase):
    """Body for POST /pincode-zones. Each pincode can be mapped only once."""


class PincodeZoneUpdate(UpdateModel):
    pincode: str | None = Field(None, pattern=PINCODE_PATTERN)
    warehouse_id: ObjectIdStr | None = None


class PincodeZoneOut(PincodeZoneBase):
    id: str
