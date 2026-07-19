from bson import ObjectId
from fastapi import APIRouter
from app.db import database

router = APIRouter()

@router.get("/search")
async def search_medicine(pincode: str, medicine_name: str):
    
    zone = await database["pincode_zones"].find_one({"pincode": pincode})
    if not zone:
        return {"error": "Pincode not serviceable"}
    
    warehouse_id = zone["warehouse_id"]
    
    medicine = await database["medicines"].find_one({"name": medicine_name})
    if not medicine:
        return {"error": "Medicine not found"}
    
    medicine_id = str(medicine["_id"])
    
    inventory_item = await database["inventory"].find_one({
    "store_id": warehouse_id,
    "medicine_id": medicine_id
})
    
    if not inventory_item:
        return {"error": "This medicine is not available in your area"}
    
    return {
        "medicine_name": medicine["name"],
        "price": inventory_item["price"],
        "quantity_available": inventory_item["quantity"]
    }