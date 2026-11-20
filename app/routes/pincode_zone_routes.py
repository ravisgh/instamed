from fastapi import APIRouter, Depends, status

from app.core import crud
from app.core.pagination import Pagination
from app.db import get_db
from app.models.pincode_zone import PincodeZoneCreate, PincodeZoneOut, PincodeZoneUpdate

router = APIRouter(prefix="/pincode-zones", tags=["Pincode zones"])

RESOURCE = "Pincode zone"
WAREHOUSE = "Warehouse"


@router.post("", response_model=PincodeZoneOut, status_code=status.HTTP_201_CREATED)
async def create_pincode_zone(zone: PincodeZoneCreate, db=Depends(get_db)):
    await crud.ensure_exists(db["stores"], zone.warehouse_id, WAREHOUSE)
    return await crud.insert(db["pincode_zones"], zone.model_dump(mode="json"), RESOURCE)


@router.get("", response_model=list[PincodeZoneOut])
async def list_pincode_zones(page: Pagination = Depends(), db=Depends(get_db)):
    return await crud.list_page(db["pincode_zones"], page)


@router.get("/{zone_id}", response_model=PincodeZoneOut)
async def get_pincode_zone(zone_id: str, db=Depends(get_db)):
    return await crud.get_or_404(db["pincode_zones"], zone_id, RESOURCE)


@router.patch("/{zone_id}", response_model=PincodeZoneOut)
async def update_pincode_zone(zone_id: str, changes: PincodeZoneUpdate, db=Depends(get_db)):
    if changes.warehouse_id is not None:
        await crud.ensure_exists(db["stores"], changes.warehouse_id, WAREHOUSE)
    return await crud.update_or_404(db["pincode_zones"], zone_id, changes.changes(), RESOURCE)


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pincode_zone(zone_id: str, db=Depends(get_db)):
    await crud.delete_or_404(db["pincode_zones"], zone_id, RESOURCE)
