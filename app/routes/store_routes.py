from bson import ObjectId
from fastapi import APIRouter
from app.db import database
from app.models.store import Store

router = APIRouter()

@router.post("/stores")
async def create_store(store: Store):
    store_dict = store.dict()
    result = await database["stores"].insert_one(store_dict)
    return {"id": str(result.inserted_id), "message": "Store added successfully"}

@router.get("/stores")
async def get_stores():
    stores = []
    async for store in database["stores"].find():
        store["_id"] = str(store["_id"])
        stores.append(store)
    return stores