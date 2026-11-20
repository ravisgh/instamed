"""Helpers for MongoDB ObjectIds.

Mongo stores ids as ObjectId; the API exposes them as 24-char hex strings.
"""

from typing import Annotated, Any

from bson import ObjectId
from fastapi import HTTPException, status
from pydantic import AfterValidator


def parse_object_id(value: str) -> ObjectId:
    """Turn a path parameter into an ObjectId, or answer 400 if it is malformed."""
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id")
    return ObjectId(value)


def _check_object_id(value: str) -> str:
    if not ObjectId.is_valid(value):
        raise ValueError("must be a 24-character hex ObjectId")
    return value


# Use in request models for fields that reference another document (422 if malformed).
ObjectIdStr = Annotated[str, AfterValidator(_check_object_id)]


def document_to_out(doc: dict[str, Any]) -> dict[str, Any]:
    """Convert a Mongo document to API shape: `_id: ObjectId` -> `id: str`."""
    out = {key: value for key, value in doc.items() if key != "_id"}
    return {"id": str(doc["_id"]), **out}
