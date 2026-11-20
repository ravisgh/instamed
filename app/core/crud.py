"""Small, shared CRUD operations on a Mongo collection.

Every resource (medicines, stores, ...) does the same five things, so routes call
these helpers instead of repeating the same Mongo code and 404 handling.
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


async def insert(
    collection: AsyncIOMotorCollection, data: dict[str, Any], resource: str = "Item"
) -> dict[str, Any]:
    document = dict(data)  # insert_one adds `_id` to the dict it is given
    try:
        result = await collection.insert_one(document)
    except DuplicateKeyError:
        raise conflict(resource) from None
    return document_to_out({**document, "_id": result.inserted_id})


async def ensure_exists(collection: AsyncIOMotorCollection, item_id: str, resource: str) -> None:
    """404 unless a document with this id exists (used for references like medicine_id)."""
    if await collection.count_documents({"_id": parse_object_id(item_id)}, limit=1) == 0:
        raise not_found(resource)


async def list_page(
    collection: AsyncIOMotorCollection, page: Pagination, query: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    cursor = collection.find(query or {}).sort("_id", 1).skip(page.skip).limit(page.limit)
    return [document_to_out(doc) async for doc in cursor]


async def get_or_404(
    collection: AsyncIOMotorCollection, item_id: str, resource: str
) -> dict[str, Any]:
    document = await collection.find_one({"_id": parse_object_id(item_id)})
    if document is None:
        raise not_found(resource)
    return document_to_out(document)


async def update_or_404(
    collection: AsyncIOMotorCollection, item_id: str, changes: dict[str, Any], resource: str
) -> dict[str, Any]:
    # Matching on _id (not modified_count) means re-sending identical data is still a 200.
    try:
        document = await collection.find_one_and_update(
            {"_id": parse_object_id(item_id)},
            {"$set": changes},
            return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError:
        raise conflict(resource) from None
    if document is None:
        raise not_found(resource)
    return document_to_out(document)


async def delete_or_404(collection: AsyncIOMotorCollection, item_id: str, resource: str) -> None:
    result = await collection.delete_one({"_id": parse_object_id(item_id)})
    if result.deleted_count == 0:
        raise not_found(resource)
