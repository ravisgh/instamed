"""FastAPI dependencies that hand out one repository per collection."""

from typing import Annotated

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_db
from app.repositories.base import MongoRepository


class Repositories:
    """All repositories for one request, built from the request's database."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.medicines = MongoRepository(db["medicines"], "Medicine")
        self.stores = MongoRepository(db["stores"], "Store")
        self.warehouses = MongoRepository(db["stores"], "Warehouse")  # same data, own 404 text
        self.inventory = MongoRepository(db["inventory"], "Inventory item")
        self.pincode_zones = MongoRepository(db["pincode_zones"], "Pincode zone")


def get_repos(db: AsyncIOMotorDatabase = Depends(get_db)) -> Repositories:
    return Repositories(db)


# Use as a parameter type in routes: `repos: Repos`.
Repos = Annotated[Repositories, Depends(get_repos)]
