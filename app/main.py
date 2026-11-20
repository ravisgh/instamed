from fastapi import FastAPI

from app.core import middleware
from app.core.config import Settings, get_settings
from app.core.logging import setup_logging
from app.core.rate_limit import RateLimiter
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


def create_app(settings: Settings) -> FastAPI:
    """Build the FastAPI app for the given settings (tests build variants of it)."""
    setup_logging(settings.log_level)
    docs = settings.show_docs
    app = FastAPI(
        title=settings.app_name,
        version="0.8.0",
        lifespan=lifespan,
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )
    app.state.settings = settings
    app.state.rate_limiter = RateLimiter()
    middleware.install(app, settings)
    for router in (
        health_router,
        auth_router,
        user_router,
        medicine_router,
        store_router,
        inventory_router,
        pincode_zone_router,
        search_router,
        prescription_router,
        order_router,
    ):
        app.include_router(router)
    app.add_api_route("/", read_root, methods=["GET"], include_in_schema=False)
    return app


def read_root():
    return {"message": "InstaMed backend is running!"}


app = create_app(get_settings())
