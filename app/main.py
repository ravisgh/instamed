from fastapi import FastAPI
from app.db import database
from app.routes.medicine_routes import router as medicine_router
from app.routes.store_routes import router as store_router
from app.routes.inventory_routes import router as inventory_router
from app.routes.pincode_zone_routes import router as pincode_zone_router


app = FastAPI()

app.include_router(medicine_router)
app.include_router(store_router)
app.include_router(inventory_router)
app.include_router(pincode_zone_router)


@app.get("/")
def read_root():
    return {"message": "InstaMed backend is running!"}

@app.get("/test-db")
async def test_db():
    collections = await database.list_collection_names()
    return {"collections": collections}