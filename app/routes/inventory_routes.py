from bson import ObjectId
from fastapi import APIRouter
from app.db import database
from app.models.inventory import Inventory

router = APIRouter()

@router.post("/inventory")
async def create_inventory(inventory: Inventory):
    inventory_dict = inventory.dict()
    result = await database["inventory"].insert_one(inventory_dict)
    return {"id": str(result.inserted_id), "message": "inventory added successfully"}

@router.get("/inventory")
async def get_inventory():
    inventory_list = []
    async for inventory in database["inventory"].find():
        inventory["_id"] = str (inventory["_id"])
        inventory_list.append(inventory)
    return inventory_list
    