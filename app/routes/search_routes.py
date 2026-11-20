from fastapi import APIRouter, Query

from app.models.pincode_zone import PINCODE_PATTERN
from app.repositories import Repos
from app.services.search import SearchResult, find_stock

router = APIRouter(tags=["Search"])


@router.get("/search", response_model=SearchResult)
async def search_medicine(
    repos: Repos,
    pincode: str = Query(pattern=PINCODE_PATTERN, examples=["560038"]),
    medicine_name: str = Query(min_length=1, max_length=200),
):
    """Pincode -> serving warehouse -> medicine (by exact name, any case) -> stock there."""
    return await find_stock(repos, pincode, medicine_name)
