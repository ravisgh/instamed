from fastapi import APIRouter, Depends, status

from app.core import crud
from app.core.pagination import Pagination
from app.db import get_db
from app.models.medicine import MedicineCreate, MedicineOut, MedicineUpdate

router = APIRouter(prefix="/medicines", tags=["Medicines"])

RESOURCE = "Medicine"


@router.post("", response_model=MedicineOut, status_code=status.HTTP_201_CREATED)
async def create_medicine(medicine: MedicineCreate, db=Depends(get_db)):
    return await crud.insert(db["medicines"], medicine.model_dump(mode="json"), RESOURCE)


@router.get("", response_model=list[MedicineOut])
async def list_medicines(page: Pagination = Depends(), db=Depends(get_db)):
    return await crud.list_page(db["medicines"], page)


@router.get("/{medicine_id}", response_model=MedicineOut)
async def get_medicine(medicine_id: str, db=Depends(get_db)):
    return await crud.get_or_404(db["medicines"], medicine_id, RESOURCE)


@router.patch("/{medicine_id}", response_model=MedicineOut)
async def update_medicine(medicine_id: str, changes: MedicineUpdate, db=Depends(get_db)):
    return await crud.update_or_404(db["medicines"], medicine_id, changes.changes(), RESOURCE)


@router.delete("/{medicine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medicine(medicine_id: str, db=Depends(get_db)):
    await crud.delete_or_404(db["medicines"], medicine_id, RESOURCE)
