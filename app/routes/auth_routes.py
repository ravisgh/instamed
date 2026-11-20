from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.auth import CurrentUser
from app.core.rate_limit import client_ip, enforce
from app.core.security import create_access_token
from app.models.user import Token, UserOut, UserRegister
from app.repositories import Repos
from app.services import users

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(body: UserRegister, repos: Repos, request: Request):
    """Create a customer account."""
    settings = request.app.state.settings
    enforce(
        request,
        f"register:ip:{client_ip(request)}",
        settings.registrations_per_ip_per_hour,
        window=3600,
    )
    return await users.create_user(repos, body)


@router.post("/login", response_model=Token)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()], repos: Repos, request: Request
):
    """OAuth2 password flow: send `username` (your email) and `password` as form fields."""
    settings = request.app.state.settings
    email = form.username.strip().lower()
    enforce(
        request, f"login:ip:{client_ip(request)}", settings.login_attempts_per_ip_per_minute, 60
    )
    enforce(request, f"login:email:{email}", settings.login_attempts_per_email_per_minute, 60)
    user = await users.authenticate(repos, email, form.password)
    return Token(access_token=create_access_token(user["id"], user["role"]))


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser):
    return user
