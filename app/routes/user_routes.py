from fastapi import APIRouter, Depends, status

from app.core.auth import AdminOnly
from app.core.pagination import Pagination
from app.models.user import UserCreate, UserOut, UserUpdate
from app.repositories import Repos
from app.services import users

router = APIRouter(prefix="/users", tags=["Users (admin)"], dependencies=[AdminOnly])


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(body: UserCreate, repos: Repos):
    return await users.create_user(repos, body)


@router.get("", response_model=list[UserOut])
async def list_users(repos: Repos, page: Pagination = Depends()):
    return await repos.users.list_page(page)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str, repos: Repos):
    return await repos.users.get(user_id)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(user_id: str, changes: UserUpdate, repos: Repos):
    return await repos.users.update(user_id, changes.changes())
