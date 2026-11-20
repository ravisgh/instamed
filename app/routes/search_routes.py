import re

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.db import get_db
from app.models.pincode_zone import PINCODE_PATTERN

router = APIRouter(tags=["Search"])


class SearchResult(BaseModel):
    medicine_id: str
    medicine_name: str
    price: float
    quantity_available: int


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.get("/search", response_model=SearchResult)
async def search_medicine(
    pincode: str = Query(pattern=PINCODE_PATTERN, examples=["560038"]),
    medicine_name: str = Query(min_length=1, max_length=200),
    db=Depends(get_db),
):
    """Pincode -> serving warehouse -> medicine (by exact name, any case) -> stock there."""
    zone = await db["pincode_zones"].find_one({"pincode": pincode})
    if zone is None:
        raise _not_found("Pincode not serviceable")

    # re.escape stops user input being treated as a regex (".*" would match everything).
    name_pattern = f"^{re.escape(medicine_name.strip())}$"
    medicine = await db["medicines"].find_one({"name": {"$regex": name_pattern, "$options": "i"}})
    if medicine is None:
        raise _not_found("Medicine not found")

    medicine_id = str(medicine["_id"])
    item = await db["inventory"].find_one(
        {"store_id": zone["warehouse_id"], "medicine_id": medicine_id}
    )
    if item is None:
        raise _not_found("Medicine not available in your area")

    return SearchResult(
        medicine_id=medicine_id,
        medicine_name=medicine["name"],
        price=item["price"],
        quantity_available=item["quantity"],
    )
