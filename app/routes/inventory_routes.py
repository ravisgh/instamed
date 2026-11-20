from fastapi import APIRouter, Depends

from app.db import get_db
from app.models.inventory import Inventory

router = APIRouter()

@router.post("/inventory")
async def create_inventory(inventory: Inventory, db=Depends(get_db)):
    inventory_dict = inventory.dict()
    result = await db["inventory"].insert_one(inventory_dict)
    return {"id": str(result.inserted_id), "message": "inventory added successfully"}

@router.get("/inventory")
async def get_inventory(db=Depends(get_db)):
    inventory_list = []
    async for inventory in db["inventory"].find():
        inventory["_id"] = str (inventory["_id"])
        inventory_list.append(inventory)
    return inventory_list
    