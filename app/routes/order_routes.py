from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.auth import CurrentUser, StaffOnly
from app.core.pagination import Pagination
from app.models.order import OrderCreate, OrderOut, OrderStatus, OrderStatusUpdate
from app.repositories import Repos
from app.services import orders
from app.services.prescriptions import is_staff

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def place_order(body: OrderCreate, user: CurrentUser, repos: Repos):
    """Reserve stock at the store serving `pincode` and create the order."""
    return await orders.place_order(repos, user, body)


@router.get("", response_model=list[OrderOut])
async def list_orders(
    user: CurrentUser,
    repos: Repos,
    page: Pagination = Depends(),
    status_filter: Annotated[OrderStatus | None, Query(alias="status")] = None,
):
    """Customers see their own orders; staff see all."""
    query: dict = {} if is_staff(user) else {"user_id": user["id"]}
    if status_filter:
        query["status"] = status_filter
    return await repos.orders.list_page(page, query)


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: str, user: CurrentUser, repos: Repos):
    return await orders.get_visible(repos, user, order_id)


@router.post("/{order_id}/cancel", response_model=OrderOut)
async def cancel_order(order_id: str, user: CurrentUser, repos: Repos):
    """Customers may cancel until dispatch; staff until delivery. Stock is put back."""
    return await orders.cancel(repos, user, order_id)


@router.patch("/{order_id}/status", response_model=OrderOut, dependencies=[StaffOnly])
async def update_order_status(
    order_id: str, body: OrderStatusUpdate, user: CurrentUser, repos: Repos
):
    """placed -> confirmed -> dispatched -> delivered, one step at a time."""
    return await orders.advance(repos, user, order_id, body.status)
