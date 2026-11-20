"""Prescription uploads (stored on local disk) and pharmacist review."""

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status
from pymongo import ReturnDocument
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.ids import document_to_out, parse_object_id
from app.models.prescription import PrescriptionReview
from app.repositories import Repositories

STAFF_ROLES = {"admin", "pharmacist"}

# Declared type -> (file extension, magic bytes the content must start with).
ALLOWED_TYPES: dict[str, tuple[str, bytes]] = {
    "application/pdf": (".pdf", b"%PDF"),
    "image/jpeg": (".jpg", b"\xff\xd8\xff"),
    "image/png": (".png", b"\x89PNG\r\n\x1a\n"),
}


def is_staff(user: dict[str, Any]) -> bool:
    return user["role"] in STAFF_ROLES


def upload_dir() -> Path:
    path = Path(get_settings().upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


async def store_upload(repos: Repositories, user: dict[str, Any], file: UploadFile) -> dict:
    settings = get_settings()
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload a PDF, JPEG or PNG",
        )
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File is larger than {settings.max_upload_bytes // (1024 * 1024)} MB",
        )
    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="File is empty"
        )
    extension, magic = ALLOWED_TYPES[content_type]
    if not data.startswith(magic):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File content does not match its type",
        )

    # Random server-side name: never trust or reuse the client's filename on disk.
    stored_name = f"{uuid.uuid4().hex}{extension}"
    await run_in_threadpool((upload_dir() / stored_name).write_bytes, data)
    return await repos.prescriptions.insert(
        {
            "user_id": user["id"],
            "original_filename": Path(file.filename or "prescription").name[:200],
            "stored_name": stored_name,
            "content_type": content_type,
            "size_bytes": len(data),
            "status": "pending",
            "note": None,
            "reviewed_by": None,
            "uploaded_at": datetime.now(UTC),
            "reviewed_at": None,
        }
    )


async def get_visible(repos: Repositories, user: dict[str, Any], prescription_id: str) -> dict:
    """The prescription if the user owns it or is staff; 404 otherwise (no existence leak)."""
    rx = await repos.prescriptions.get(prescription_id)
    if not is_staff(user) and rx["user_id"] != user["id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")
    return rx


def file_path(rx: dict[str, Any]) -> Path:
    return upload_dir() / rx["stored_name"]


async def review(
    repos: Repositories, reviewer: dict[str, Any], prescription_id: str, body: PrescriptionReview
) -> dict:
    oid = parse_object_id(prescription_id)
    document = await repos.prescriptions.collection.find_one_and_update(
        {"_id": oid, "status": "pending"},
        {
            "$set": {
                "status": body.status,
                "note": body.note,
                "reviewed_by": reviewer["id"],
                "reviewed_at": datetime.now(UTC),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if document is None:
        await repos.prescriptions.get(prescription_id)  # 404 if it does not exist at all
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already reviewed")
    return document_to_out(document)
