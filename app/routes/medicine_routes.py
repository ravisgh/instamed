from fastapi import APIRouter, Depends, status

from app.core.auth import StaffOnly
from app.core.pagination import Pagination
from app.models.medicine import MedicineCreate, MedicineOut, MedicineUpdate
from app.repositories import Repos

router = APIRouter(prefix="/medicines", tags=["Medicines"])


@router.post(
    "", dependencies=[StaffOnly], response_model=MedicineOut, status_code=status.HTTP_201_CREATED
)
async def create_medicine(medicine: MedicineCreate, repos: Repos):
    return await repos.medicines.insert(medicine.model_dump(mode="json"))


@router.get("", response_model=list[MedicineOut])
async def list_medicines(repos: Repos, page: Pagination = Depends()):
    return await repos.medicines.list_page(page)


@router.get("/{medicine_id}", response_model=MedicineOut)
async def get_medicine(medicine_id: str, repos: Repos):
    return await repos.medicines.get(medicine_id)


@router.patch("/{medicine_id}", dependencies=[StaffOnly], response_model=MedicineOut)
async def update_medicine(medicine_id: str, changes: MedicineUpdate, repos: Repos):
    return await repos.medicines.update(medicine_id, changes.changes())


@router.delete("/{medicine_id}", dependencies=[StaffOnly], status_code=status.HTTP_204_NO_CONTENT)
async def delete_medicine(medicine_id: str, repos: Repos):
    await repos.medicines.delete(medicine_id)
