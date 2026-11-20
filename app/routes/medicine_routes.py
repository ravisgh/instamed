from bson import ObjectId
from fastapi import APIRouter, Depends

from app.db import get_db
from app.models.medicine import Medicine

router = APIRouter()

@router.post("/medicines")
async def create_medicine(medicine: Medicine, db=Depends(get_db)):
    medicine_dict = medicine.dict()
    result = await db["medicines"].insert_one(medicine_dict)
    return {"id": str(result.inserted_id), "message": "Medicine added successfully"}

@router.get("/medicines")
async def get_medicines(db=Depends(get_db)):
    medicines = []
    async for medicine in db["medicines"].find():
        medicine["_id"] = str(medicine["_id"])
        medicines.append(medicine)
    return medicines

@router.get("/medicines/{medicine_id}")
async def get_medicine(medicine_id: str, db=Depends(get_db)):
    medicine = await db["medicines"].find_one({"_id": ObjectId(medicine_id)})
    if medicine:
        medicine["_id"] = str(medicine["_id"])
        return medicine
    return {"error": "Medicine not found"}

@router.put("/medicines/{medicine_id}")
async def update_medicine(medicine_id: str, medicine: Medicine, db=Depends(get_db)):
    updated_data = medicine.dict()
    result = await db["medicines"].update_one(
        {"_id": ObjectId(medicine_id)},
        {"$set": updated_data}
    )
    if result.modified_count:
        return {"message": "Medicine updated successfully"}
    return {"error": "Medicine not found or no changes made"}

@router.delete("/medicines/{medicine_id}")
async def delete_medicine(medicine_id: str, db=Depends(get_db)):
    result = await db["medicines"].delete_one({"_id": ObjectId(medicine_id)})
    if result.deleted_count:
        return {"message": "Medicine deleted successfully"}
    return {"error": "Medicine not found"}