from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

PrescriptionStatus = Literal["pending", "approved", "rejected"]


class PrescriptionReview(BaseModel):
    """Body for PATCH /prescriptions/{id}/review (staff only)."""

    status: Literal["approved", "rejected"]
    note: str | None = Field(None, max_length=500)


class PrescriptionOut(BaseModel):
    id: str
    user_id: str
    original_filename: str
    content_type: str
    size_bytes: int
    status: PrescriptionStatus
    note: str | None = None
    reviewed_by: str | None = None
    uploaded_at: datetime
    reviewed_at: datetime | None = None
