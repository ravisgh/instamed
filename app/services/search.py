"""Pincode -> serving warehouse -> every pack size of a medicine -> stock there."""

import re

from fastapi import HTTPException, status
from pydantic import BaseModel

from app.repositories import Repositories


class SearchHit(BaseModel):
    medicine_id: str
    name: str
    pack_size: str
    mrp: float
    price: float
    quantity_available: int
    prescription_required: bool


class SearchResponse(BaseModel):
    pincode: str
    store_id: str
    results: list[SearchHit]


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def exact_name_query(name: str) -> dict:
    """Case-insensitive exact match; re.escape stops input acting as a regex ('.*')."""
    return {"name": {"$regex": f"^{re.escape(name.strip())}$", "$options": "i"}}


async def find_stock(repos: Repositories, pincode: str, medicine_name: str) -> SearchResponse:
    zone = await repos.pincode_zones.find_one({"pincode": pincode})
    if zone is None:
        raise _not_found("Pincode not serviceable")

    medicines = {
        str(doc["_id"]): doc
        async for doc in repos.medicines.collection.find(exact_name_query(medicine_name))
    }
    if not medicines:
        raise _not_found("Medicine not found")

    store_id = zone["warehouse_id"]
    hits = [
        SearchHit(
            medicine_id=row["medicine_id"],
            name=medicines[row["medicine_id"]]["name"],
            pack_size=medicines[row["medicine_id"]]["pack_size"],
            mrp=medicines[row["medicine_id"]]["mrp"],
            price=row["price"],
            quantity_available=row["quantity"],
            prescription_required=medicines[row["medicine_id"]]["prescription_required"],
        )
        async for row in repos.inventory.collection.find(
            {"store_id": store_id, "medicine_id": {"$in": list(medicines)}, "quantity": {"$gt": 0}}
        )
    ]
    if not hits:
        raise _not_found("Medicine not available in your area")

    hits.sort(key=lambda hit: (hit.price, hit.pack_size))
    return SearchResponse(pincode=pincode, store_id=store_id, results=hits)
