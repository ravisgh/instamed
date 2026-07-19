from bson import ObjectId
from fastapi import APIRouter
from app.db import database
from app.models.pincode_zone import Pincode_Zone

router = APIRouter()

@router.post("/pincode_zone")
async def create_pincode_zone(pincode_zone: Pincode_Zone):
    pincode_zone_dict = pincode_zone.dict()
    result = await database["pincode_zones"].insert_one(pincode_zone_dict)
    return {"id": str(result.inserted_id), "message": "Pincode zone added successfully"}

@router.get("/pincode-zone")
async def get_pincode_zones():
    pincode_zone_list = []
    async for pincode_zone in database["pincode_zones"].find():
        pincode_zone["_id"] = str(pincode_zone["_id"])
        pincode_zone_list.append(pincode_zone)
    return pincode_zone_list
    