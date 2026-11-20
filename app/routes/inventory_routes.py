from fastapi import APIRouter, Depends, status

from app.core.auth import StaffOnly
from app.core.pagination import Pagination
from app.models.inventory import InventoryCreate, InventoryOut, InventoryUpdate
from app.repositories import Repos
from app.services import catalog

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.post(
    "", dependencies=[StaffOnly], response_model=InventoryOut, status_code=status.HTTP_201_CREATED
)
async def create_inventory(item: InventoryCreate, repos: Repos):
    return await catalog.create_inventory(repos, item)


@router.get("", response_model=list[InventoryOut])
async def list_inventory(repos: Repos, page: Pagination = Depends()):
    return await repos.inventory.list_page(page)


@router.get("/{item_id}", response_model=InventoryOut)
async def get_inventory_item(item_id: str, repos: Repos):
    return await repos.inventory.get(item_id)


@router.patch("/{item_id}", dependencies=[StaffOnly], response_model=InventoryOut)
async def update_inventory_item(item_id: str, changes: InventoryUpdate, repos: Repos):
    return await repos.inventory.update(item_id, changes.changes())


@router.delete("/{item_id}", dependencies=[StaffOnly], status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(item_id: str, repos: Repos):
    await repos.inventory.delete(item_id)
