"""Pincode -> serving warehouse -> medicine -> stock at that warehouse."""

import re

from fastapi import HTTPException, status
from pydantic import BaseModel

from app.repositories import Repositories


class SearchResult(BaseModel):
    medicine_id: str
    medicine_name: str
    price: float
    quantity_available: int


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


async def find_stock(repos: Repositories, pincode: str, medicine_name: str) -> SearchResult:
    zone = await repos.pincode_zones.find_one({"pincode": pincode})
    if zone is None:
        raise _not_found("Pincode not serviceable")

    # re.escape stops user input being treated as a regex (".*" would match everything).
    name_pattern = f"^{re.escape(medicine_name.strip())}$"
    medicine = await repos.medicines.find_one({"name": {"$regex": name_pattern, "$options": "i"}})
    if medicine is None:
        raise _not_found("Medicine not found")

    item = await repos.inventory.find_one(
        {"store_id": zone["warehouse_id"], "medicine_id": medicine["id"]}
    )
    if item is None:
        raise _not_found("Medicine not available in your area")

    return SearchResult(
        medicine_id=medicine["id"],
        medicine_name=medicine["name"],
        price=item["price"],
        quantity_available=item["quantity"],
    )
