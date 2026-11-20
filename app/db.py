from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings


async def create_indexes(db: AsyncIOMotorDatabase) -> None:
    """Indexes the app relies on. create_index is a no-op if the index already exists."""
    await db["pincode_zones"].create_index("pincode", unique=True)
    await db["medicines"].create_index("name")
    # One inventory row per medicine per store.
    await db["inventory"].create_index([("store_id", 1), ("medicine_id", 1)], unique=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open one Mongo client when the app starts and close it when the app stops.

    Creating the client here (not at import time) ties it to the running event loop,
    which keeps tests and reloads from sharing a client across loops.
    """
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongo_uri)
    app.state.db = client[settings.db_name]
    await create_indexes(app.state.db)
    try:
        yield
    finally:
        client.close()


def get_db(request: Request) -> AsyncIOMotorDatabase:
    """FastAPI dependency: the database opened in lifespan."""
    return request.app.state.db
