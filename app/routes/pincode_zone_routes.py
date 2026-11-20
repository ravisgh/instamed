from fastapi import APIRouter, Depends, status

from app.core.pagination import Pagination
from app.models.pincode_zone import PincodeZoneCreate, PincodeZoneOut, PincodeZoneUpdate
from app.repositories import Repos
from app.services import catalog

router = APIRouter(prefix="/pincode-zones", tags=["Pincode zones"])


@router.post("", response_model=PincodeZoneOut, status_code=status.HTTP_201_CREATED)
async def create_pincode_zone(zone: PincodeZoneCreate, repos: Repos):
    return await catalog.create_pincode_zone(repos, zone)


@router.get("", response_model=list[PincodeZoneOut])
async def list_pincode_zones(repos: Repos, page: Pagination = Depends()):
    return await repos.pincode_zones.list_page(page)


@router.get("/{zone_id}", response_model=PincodeZoneOut)
async def get_pincode_zone(zone_id: str, repos: Repos):
    return await repos.pincode_zones.get(zone_id)


@router.patch("/{zone_id}", response_model=PincodeZoneOut)
async def update_pincode_zone(zone_id: str, changes: PincodeZoneUpdate, repos: Repos):
    return await catalog.update_pincode_zone(repos, zone_id, changes)


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pincode_zone(zone_id: str, repos: Repos):
    await repos.pincode_zones.delete(zone_id)
