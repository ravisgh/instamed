from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.core.auth import CurrentUser, StaffOnly
from app.core.pagination import Pagination
from app.models.prescription import PrescriptionOut, PrescriptionReview, PrescriptionStatus
from app.repositories import Repos
from app.services import prescriptions

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])


@router.post("", response_model=PrescriptionOut, status_code=status.HTTP_201_CREATED)
async def upload_prescription(
    user: CurrentUser,
    repos: Repos,
    file: Annotated[UploadFile, File(description="PDF, JPEG or PNG, up to 5 MB")],
):
    return await prescriptions.store_upload(repos, user, file)


@router.get("", response_model=list[PrescriptionOut])
async def list_prescriptions(
    user: CurrentUser,
    repos: Repos,
    page: Pagination = Depends(),
    status_filter: Annotated[PrescriptionStatus | None, Query(alias="status")] = None,
):
    """Customers see their own; staff see everyone's."""
    query: dict = {} if prescriptions.is_staff(user) else {"user_id": user["id"]}
    if status_filter:
        query["status"] = status_filter
    return await repos.prescriptions.list_page(page, query)


@router.get("/{prescription_id}", response_model=PrescriptionOut)
async def get_prescription(prescription_id: str, user: CurrentUser, repos: Repos):
    return await prescriptions.get_visible(repos, user, prescription_id)


@router.get("/{prescription_id}/file", response_class=FileResponse)
async def download_prescription(prescription_id: str, user: CurrentUser, repos: Repos):
    rx = await prescriptions.get_visible(repos, user, prescription_id)
    return FileResponse(
        prescriptions.file_path(rx),
        media_type=rx["content_type"],
        filename=rx["original_filename"],
    )


@router.patch("/{prescription_id}/review", response_model=PrescriptionOut, dependencies=[StaffOnly])
async def review_prescription(
    prescription_id: str, body: PrescriptionReview, user: CurrentUser, repos: Repos
):
    return await prescriptions.review(repos, user, prescription_id, body)
