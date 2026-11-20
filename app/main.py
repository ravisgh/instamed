from fastapi import FastAPI

from app.core import middleware
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db import lifespan
from app.routes.auth_routes import router as auth_router
from app.routes.health_routes import router as health_router
from app.routes.inventory_routes import router as inventory_router
from app.routes.medicine_routes import router as medicine_router
from app.routes.order_routes import router as order_router
from app.routes.pincode_zone_routes import router as pincode_zone_router
from app.routes.prescription_routes import router as prescription_router
from app.routes.search_routes import router as search_router
from app.routes.store_routes import router as store_router
from app.routes.user_routes import router as user_router

settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(title=settings.app_name, version="0.6.0", lifespan=lifespan)
middleware.install(app)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(medicine_router)
app.include_router(store_router)
app.include_router(inventory_router)
app.include_router(pincode_zone_router)
app.include_router(search_router)
app.include_router(prescription_router)
app.include_router(order_router)


@app.get("/")
def read_root():
    return {"message": "InstaMed backend is running!"}
