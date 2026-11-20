"""Data-access layer: the only place that talks to Mongo collections directly.

A repository wraps one collection and speaks in API-shaped dicts (`id: str`),
raising 404/409 HTTP errors so routes and services stay free of Mongo details.
"""

from typing import Any

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.core.ids import document_to_out, parse_object_id
from app.core.pagination import Pagination


def not_found(resource: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource} not found")


def conflict(resource: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{resource} already exists")


class MongoRepository:
    def __init__(self, collection: AsyncIOMotorCollection, resource: str):
        self.collection = collection
        self.resource = resource

    async def insert(self, data: dict[str, Any]) -> dict[str, Any]:
        document = dict(data)  # insert_one adds `_id` to the dict it is given
        try:
            result = await self.collection.insert_one(document)
        except DuplicateKeyError:
            raise conflict(self.resource) from None
        return document_to_out({**document, "_id": result.inserted_id})

    async def list_page(
        self, page: Pagination, query: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        cursor = self.collection.find(query or {}).sort("_id", 1).skip(page.skip).limit(page.limit)
        return [document_to_out(doc) async for doc in cursor]

    async def get(self, item_id: str) -> dict[str, Any]:
        document = await self.collection.find_one({"_id": parse_object_id(item_id)})
        if document is None:
            raise not_found(self.resource)
        return document_to_out(document)

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        document = await self.collection.find_one(query)
        return document_to_out(document) if document else None

    async def update(self, item_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        # Matching on _id (not modified_count) means re-sending identical data is still a 200.
        try:
            document = await self.collection.find_one_and_update(
                {"_id": parse_object_id(item_id)},
                {"$set": changes},
                return_document=ReturnDocument.AFTER,
            )
        except DuplicateKeyError:
            raise conflict(self.resource) from None
        if document is None:
            raise not_found(self.resource)
        return document_to_out(document)

    async def delete(self, item_id: str) -> None:
        result = await self.collection.delete_one({"_id": parse_object_id(item_id)})
        if result.deleted_count == 0:
            raise not_found(self.resource)

    async def ensure_exists(self, item_id: str) -> None:
        """404 unless a document with this id exists (used for references)."""
        found = await self.collection.count_documents({"_id": parse_object_id(item_id)}, limit=1)
        if not found:
            raise not_found(self.resource)
