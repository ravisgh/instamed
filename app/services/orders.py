"""Placing, cancelling and progressing orders.

Stock is reserved with one conditional `$inc` per line
(`quantity >= wanted` -> `quantity -= wanted`), which MongoDB applies atomically, so two
orders can never take the same last pack. If a later line fails, earlier lines are put
back (a compensating update) before the error is returned.
"""

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from fastapi import HTTPException, status
from pymongo import ReturnDocument

from app.core.ids import document_to_out, parse_object_id
from app.core.logging import get_logger
from app.models.order import (
    CUSTOMER_CANCELLABLE,
    NEXT_STATUS,
    STAFF_CANCELLABLE,
    OrderCreate,
)
from app.repositories import Repositories
from app.services.prescriptions import is_staff

log = get_logger("orders")


def _error(code: int, detail: str) -> HTTPException:
    return HTTPException(status_code=code, detail=detail)


def _history(state: str, user: dict[str, Any], at: datetime) -> dict[str, Any]:
    return {"status": state, "at": at, "by": user["id"]}


async def _release(repos: Repositories, store_id: str, lines: list[tuple[str, int]]) -> None:
    for medicine_id, quantity in lines:
        await repos.inventory.collection.update_one(
            {"store_id": store_id, "medicine_id": medicine_id}, {"$inc": {"quantity": quantity}}
        )


async def _check_prescription(
    repos: Repositories, user: dict[str, Any], prescription_id: str | None
) -> None:
    rx = None
    if prescription_id:
        rx = await repos.prescriptions.find_one({"_id": ObjectId(prescription_id)})
    if rx is None or rx["user_id"] != user["id"] or rx["status"] != "approved":
        raise _error(
            status.HTTP_400_BAD_REQUEST,
            "An approved prescription of yours is required for prescription medicines",
        )


async def place_order(repos: Repositories, user: dict[str, Any], body: OrderCreate) -> dict:
    zone = await repos.pincode_zones.find_one({"pincode": body.pincode})
    if zone is None:
        raise _error(status.HTTP_404_NOT_FOUND, "Pincode not serviceable")
    store_id = zone["warehouse_id"]

    medicines: dict[str, dict[str, Any]] = {}
    for item in body.items:
        medicine = await repos.medicines.find_one({"_id": ObjectId(item.medicine_id)})
        if medicine is None:
            raise _error(status.HTTP_404_NOT_FOUND, "Medicine not found")
        medicines[item.medicine_id] = medicine
    if any(m["prescription_required"] for m in medicines.values()):
        await _check_prescription(repos, user, body.prescription_id)

    reserved: list[tuple[str, int]] = []
    lines: list[dict[str, Any]] = []
    try:
        for item in body.items:
            row = await repos.inventory.collection.find_one_and_update(
                {
                    "store_id": store_id,
                    "medicine_id": item.medicine_id,
                    "quantity": {"$gte": item.quantity},
                },
                {"$inc": {"quantity": -item.quantity}},
                return_document=ReturnDocument.AFTER,
            )
            medicine = medicines[item.medicine_id]
            if row is None:
                raise _error(status.HTTP_409_CONFLICT, f"Insufficient stock for {medicine['name']}")
            reserved.append((item.medicine_id, item.quantity))
            lines.append(
                {
                    "medicine_id": item.medicine_id,
                    "name": medicine["name"],
                    "pack_size": medicine["pack_size"],
                    "quantity": item.quantity,
                    "unit_price": row["price"],
                    "line_total": round(row["price"] * item.quantity, 2),
                }
            )

        now = datetime.now(UTC)
        order = await repos.orders.insert(
            {
                "user_id": user["id"],
                "store_id": store_id,
                "pincode": body.pincode,
                "items": lines,
                "total": round(sum(line["line_total"] for line in lines), 2),
                "status": "placed",
                "prescription_id": body.prescription_id,
                "created_at": now,
                "updated_at": now,
                "history": [_history("placed", user, now)],
            }
        )
    except BaseException:
        await _release(repos, store_id, reserved)
        raise
    log.info("Order %s placed: %d lines, total %.2f", order["id"], len(lines), order["total"])
    return order


async def get_visible(repos: Repositories, user: dict[str, Any], order_id: str) -> dict:
    order = await repos.orders.get(order_id)
    if not is_staff(user) and order["user_id"] != user["id"]:
        raise _error(status.HTTP_404_NOT_FOUND, "Order not found")
    return order


async def _transition(
    repos: Repositories,
    user: dict[str, Any],
    order_id: str,
    allowed_from: set[str],
    new_status: str,
) -> dict | None:
    now = datetime.now(UTC)
    document = await repos.orders.collection.find_one_and_update(
        {"_id": parse_object_id(order_id), "status": {"$in": sorted(allowed_from)}},
        {
            "$set": {"status": new_status, "updated_at": now},
            "$push": {"history": _history(new_status, user, now)},
        },
        return_document=ReturnDocument.AFTER,
    )
    return document_to_out(document) if document else None


async def cancel(repos: Repositories, user: dict[str, Any], order_id: str) -> dict:
    order = await get_visible(repos, user, order_id)
    allowed = STAFF_CANCELLABLE if is_staff(user) else CUSTOMER_CANCELLABLE
    updated = await _transition(repos, user, order_id, allowed, "cancelled")
    if updated is None:
        raise _error(
            status.HTTP_409_CONFLICT, f"Order is {order['status']} and cannot be cancelled"
        )
    await _release(
        repos, order["store_id"], [(i["medicine_id"], i["quantity"]) for i in order["items"]]
    )
    log.info("Order %s cancelled by %s", order_id, user["id"])
    return updated


async def advance(repos: Repositories, user: dict[str, Any], order_id: str, target: str) -> dict:
    previous = next(src for src, dst in NEXT_STATUS.items() if dst == target)
    updated = await _transition(repos, user, order_id, {previous}, target)
    if updated is None:
        order = await repos.orders.get(order_id)  # 404 if missing
        raise _error(
            status.HTTP_409_CONFLICT, f"Cannot move order from {order['status']} to {target}"
        )
    return updated
