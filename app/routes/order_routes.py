from bson import ObjectId
from fastapi import APIRouter, HTTPException, Body
from app.db import database
from app.models.order import Order

router = APIRouter()

# Allowed status values for an order's lifecycle.
ALLOWED_STATUSES = {
    "Pending",
    "Packed",
    "Out for Delivery",
    "Delivered",
    "Pending Verification",
}


# Create a new order: validate stock and prescription requirements,
# deduct inventory if everything checks out, then save the order.
@router.post("/orders")
async def create_order(order: Order):
    order_dict = order.dict()
    errors = []

    # 1. Check stock availability for every item before touching the DB.
    for item in order_dict["items"]:
        inventory_doc = await database["inventory"].find_one({
            "medicine_id": item["medicine_id"],
            "store_id": order_dict["warehouse_id"],
        })
        if not inventory_doc:
            errors.append(
                f"Medicine {item['medicine_id']} is not available in warehouse "
                f"{order_dict['warehouse_id']}"
            )
        elif inventory_doc["quantity"] < item["quantity"]:
            errors.append(
                f"Insufficient stock for medicine {item['medicine_id']}: "
                f"requested {item['quantity']}, available {inventory_doc['quantity']}"
            )

    # Reject the whole order if any item fails the stock check.
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})

    # 2. Deduct the ordered quantity from inventory for each item.
    for item in order_dict["items"]:
        await database["inventory"].update_one(
            {
                "medicine_id": item["medicine_id"],
                "store_id": order_dict["warehouse_id"],
            },
            {"$inc": {"quantity": -item["quantity"]}},
        )

    # 3. If any ordered medicine requires a prescription, hold the order
    #    for manual verification instead of letting it proceed straight to
    #    "Pending".
    needs_prescription = False
    for item in order_dict["items"]:
        medicine_doc = await database["medicines"].find_one(
            {"_id": item["medicine_id"]}
        )
        if medicine_doc and medicine_doc.get("prescription_required"):
            needs_prescription = True
            break

    order_dict["status"] = "Pending Verification" if needs_prescription else "Pending"

    # 4. Persist the order and return its id and final status.
    result = await database["orders"].insert_one(order_dict)
    return {
        "id": str(result.inserted_id),
        "status": order_dict["status"],
        "message": "Order created successfully",
    }


# List every order in the system, converting each _id to a string.
@router.get("/orders")
async def get_orders():
    orders = []
    async for order in database["orders"].find():
        order["_id"] = str(order["_id"])
        orders.append(order)
    return orders


# Fetch a single order by its id, or 404 if it doesn't exist.
@router.get("/orders/{order_id}")
async def get_order(order_id: str):
    order = await database["orders"].find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order["_id"] = str(order["_id"])
    return order


# Update only the status field of an existing order, rejecting any value
# outside the allowed lifecycle states.
@router.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str = Body(...)):
    if status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {sorted(ALLOWED_STATUSES)}",
        )

    result = await database["orders"].update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": status}},
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")

    return {"message": "Order status updated successfully", "status": status}