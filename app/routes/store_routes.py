from fastapi import APIRouter, Depends, status

from app.core import crud
from app.core.pagination import Pagination
from app.db import get_db
from app.models.store import StoreCreate, StoreOut, StoreUpdate

router = APIRouter(prefix="/stores", tags=["Stores"])

RESOURCE = "Store"


@router.post("", response_model=StoreOut, status_code=status.HTTP_201_CREATED)
async def create_store(store: StoreCreate, db=Depends(get_db)):
    return await crud.insert(db["stores"], store.model_dump(mode="json"))


@router.get("", response_model=list[StoreOut])
async def list_stores(page: Pagination = Depends(), db=Depends(get_db)):
    return await crud.list_page(db["stores"], page)


@router.get("/{store_id}", response_model=StoreOut)
async def get_store(store_id: str, db=Depends(get_db)):
    return await crud.get_or_404(db["stores"], store_id, RESOURCE)


@router.patch("/{store_id}", response_model=StoreOut)
async def update_store(store_id: str, changes: StoreUpdate, db=Depends(get_db)):
    return await crud.update_or_404(db["stores"], store_id, changes.changes(), RESOURCE)


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_store(store_id: str, db=Depends(get_db)):
    await crud.delete_or_404(db["stores"], store_id, RESOURCE)
