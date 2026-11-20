from fastapi import APIRouter, Depends, status

from app.core import crud
from app.core.pagination import Pagination
from app.db import get_db
from app.models.inventory import InventoryCreate, InventoryOut, InventoryUpdate

router = APIRouter(prefix="/inventory", tags=["Inventory"])

RESOURCE = "Inventory item"


@router.post("", response_model=InventoryOut, status_code=status.HTTP_201_CREATED)
async def create_inventory(item: InventoryCreate, db=Depends(get_db)):
    await crud.ensure_exists(db["medicines"], item.medicine_id, "Medicine")
    await crud.ensure_exists(db["stores"], item.store_id, "Store")
    return await crud.insert(db["inventory"], item.model_dump(mode="json"), RESOURCE)


@router.get("", response_model=list[InventoryOut])
async def list_inventory(page: Pagination = Depends(), db=Depends(get_db)):
    return await crud.list_page(db["inventory"], page)


@router.get("/{item_id}", response_model=InventoryOut)
async def get_inventory_item(item_id: str, db=Depends(get_db)):
    return await crud.get_or_404(db["inventory"], item_id, RESOURCE)


@router.patch("/{item_id}", response_model=InventoryOut)
async def update_inventory_item(item_id: str, changes: InventoryUpdate, db=Depends(get_db)):
    return await crud.update_or_404(db["inventory"], item_id, changes.changes(), RESOURCE)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(item_id: str, db=Depends(get_db)):
    await crud.delete_or_404(db["inventory"], item_id, RESOURCE)
