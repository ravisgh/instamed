from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.auth import CurrentUser
from app.core.security import create_access_token
from app.models.user import Token, UserOut, UserRegister
from app.repositories import Repos
from app.services import users

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(body: UserRegister, repos: Repos):
    """Create a customer account."""
    return await users.create_user(repos, body)


@router.post("/login", response_model=Token)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], repos: Repos):
    """OAuth2 password flow: send `username` (your email) and `password` as form fields."""
    user = await users.authenticate(repos, form.username, form.password)
    return Token(access_token=create_access_token(user["id"], user["role"]))


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser):
    return user
