from fastapi import Depends, FastAPI

from app.core.config import get_settings
from app.db import get_db, lifespan
from app.routes.inventory_routes import router as inventory_router
from app.routes.medicine_routes import router as medicine_router
from app.routes.pincode_zone_routes import router as pincode_zone_router
from app.routes.search_routes import router as search_router
from app.routes.store_routes import router as store_router

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)

app.include_router(medicine_router)
app.include_router(store_router)
app.include_router(inventory_router)
app.include_router(pincode_zone_router)
app.include_router(search_router)


@app.get("/")
def read_root():
    return {"message": "InstaMed backend is running!"}


@app.get("/test-db")
async def test_db(db=Depends(get_db)):
    collections = await db.list_collection_names()
    return {"collections": collections}
