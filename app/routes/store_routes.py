from fastapi import APIRouter, Depends, status

from app.core.auth import AdminOnly
from app.core.pagination import Pagination
from app.models.store import StoreCreate, StoreOut, StoreUpdate
from app.repositories import Repos

router = APIRouter(prefix="/stores", tags=["Stores"])


@router.post(
    "", dependencies=[AdminOnly], response_model=StoreOut, status_code=status.HTTP_201_CREATED
)
async def create_store(store: StoreCreate, repos: Repos):
    return await repos.stores.insert(store.model_dump(mode="json"))


@router.get("", response_model=list[StoreOut])
async def list_stores(repos: Repos, page: Pagination = Depends()):
    return await repos.stores.list_page(page)


@router.get("/{store_id}", response_model=StoreOut)
async def get_store(store_id: str, repos: Repos):
    return await repos.stores.get(store_id)


@router.patch("/{store_id}", dependencies=[AdminOnly], response_model=StoreOut)
async def update_store(store_id: str, changes: StoreUpdate, repos: Repos):
    return await repos.stores.update(store_id, changes.changes())


@router.delete("/{store_id}", dependencies=[AdminOnly], status_code=status.HTTP_204_NO_CONTENT)
async def delete_store(store_id: str, repos: Repos):
    await repos.stores.delete(store_id)
