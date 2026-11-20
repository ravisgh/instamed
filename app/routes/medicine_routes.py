from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from app.core.auth import StaffOnly
from app.core.pagination import Pagination
from app.db import get_search_index
from app.models.medicine import MedicineCreate, MedicineOut, MedicineUpdate
from app.repositories import Repos
from app.search_engine import MedicineIndex
from app.services import medicines

router = APIRouter(prefix="/medicines", tags=["Medicines"])

SearchIndex = Annotated[MedicineIndex | None, Depends(get_search_index)]


class MedicineSearchResponse(BaseModel):
    engine: Literal["elasticsearch", "mongo"]
    results: list[MedicineOut]


@router.post(
    "", dependencies=[StaffOnly], response_model=MedicineOut, status_code=status.HTTP_201_CREATED
)
async def create_medicine(medicine: MedicineCreate, repos: Repos, index: SearchIndex):
    return await medicines.create(repos, index, medicine)


@router.get("", response_model=list[MedicineOut])
async def list_medicines(repos: Repos, page: Pagination = Depends()):
    return await repos.medicines.list_page(page)


# Declared before "/{medicine_id}" so "search" is not taken as an id.
@router.get("/search", response_model=MedicineSearchResponse)
async def search_medicines(
    repos: Repos,
    index: SearchIndex,
    q: str = Query(min_length=2, max_length=100, description="Name, salt or manufacturer"),
    limit: int = Query(10, ge=1, le=50),
):
    """Typo-tolerant search via Elasticsearch; falls back to a MongoDB substring match."""
    engine, results = await medicines.search(repos, index, q, limit)
    return MedicineSearchResponse(engine=engine, results=results)


@router.get("/{medicine_id}", response_model=MedicineOut)
async def get_medicine(medicine_id: str, repos: Repos):
    return await repos.medicines.get(medicine_id)


@router.patch("/{medicine_id}", dependencies=[StaffOnly], response_model=MedicineOut)
async def update_medicine(
    medicine_id: str, changes: MedicineUpdate, repos: Repos, index: SearchIndex
):
    return await medicines.update(repos, index, medicine_id, changes)


@router.delete("/{medicine_id}", dependencies=[StaffOnly], status_code=status.HTTP_204_NO_CONTENT)
async def delete_medicine(medicine_id: str, repos: Repos, index: SearchIndex):
    await medicines.delete(repos, index, medicine_id)
