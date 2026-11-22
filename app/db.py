from contextlib import asynccontextmanager

from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings
from app.core.logging import get_logger
from app.search_engine import MedicineIndex


async def create_indexes(db: AsyncIOMotorDatabase) -> None:
    """Indexes the app relies on. create_index is a no-op if the index already exists."""
    await db["pincode_zones"].create_index("pincode", unique=True)
    # One catalog entry per product + pack size; also serves name lookups.
    await db["medicines"].create_index([("name", 1), ("pack_size", 1)], unique=True)
    # One inventory row per medicine per store.
    await db["inventory"].create_index([("store_id", 1), ("medicine_id", 1)], unique=True)
    await db["users"].create_index("email", unique=True)
    await db["prescriptions"].create_index([("user_id", 1), ("status", 1)])
    await db["orders"].create_index([("user_id", 1), ("status", 1)])
    await db["refresh_tokens"].create_index("token_hash", unique=True)
    await db["refresh_tokens"].create_index("family_id")
    # MongoDB deletes refresh tokens by itself once they expire.
    await db["refresh_tokens"].create_index("expires_at", expireAfterSeconds=0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open one Mongo client when the app starts and close it when the app stops.

    Creating the client here (not at import time) ties it to the running event loop,
    which keeps tests and reloads from sharing a client across loops.
    """
    settings = get_settings()
    if settings.uses_dev_jwt_secret:
        get_logger("startup").warning("JWT_SECRET is the built-in dev value; set it in production")
    client = AsyncIOMotorClient(settings.mongo_uri, serverSelectionTimeoutMS=3000, tz_aware=True)
    app.state.db = client[settings.db_name]
    await create_indexes(app.state.db)
    app.state.search_index = await _open_search_index(settings)
    try:
        yield
    finally:
        client.close()
        if app.state.search_index is not None:
            await app.state.search_index.close()


async def _open_search_index(settings) -> MedicineIndex | None:
    """Connect to Elasticsearch if configured. Startup never fails because of it."""
    if not settings.elasticsearch_url:
        return None
    index = MedicineIndex(
        AsyncElasticsearch(settings.elasticsearch_url, **MedicineIndex.CLIENT_OPTIONS),
        settings.elasticsearch_index,
        refresh=settings.elasticsearch_refresh,
        search_timeout=settings.elasticsearch_search_timeout_seconds,
        cooldown=settings.elasticsearch_cooldown_seconds,
    )
    try:
        await index.ensure_index()
    except Exception:
        get_logger("startup").warning(
            "Elasticsearch at %s unavailable; search will use MongoDB until it is back",
            settings.elasticsearch_url,
            exc_info=True,
        )
    return index


def get_db(request: Request) -> AsyncIOMotorDatabase:
    """FastAPI dependency: the database opened in lifespan."""
    return request.app.state.db


def get_search_index(request: Request) -> MedicineIndex | None:
    """FastAPI dependency: the Elasticsearch index, or None when not configured."""
    return getattr(request.app.state, "search_index", None)
