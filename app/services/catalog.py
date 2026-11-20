"""Business rules that span more than one collection."""

from typing import Any

from app.models.inventory import InventoryCreate
from app.models.pincode_zone import PincodeZoneCreate, PincodeZoneUpdate
from app.repositories import Repositories


async def create_inventory(repos: Repositories, item: InventoryCreate) -> dict[str, Any]:
    """Stock rows may only point at an existing medicine and store."""
    await repos.medicines.ensure_exists(item.medicine_id)
    await repos.stores.ensure_exists(item.store_id)
    return await repos.inventory.insert(item.model_dump(mode="json"))


async def create_pincode_zone(repos: Repositories, zone: PincodeZoneCreate) -> dict[str, Any]:
    await repos.warehouses.ensure_exists(zone.warehouse_id)
    return await repos.pincode_zones.insert(zone.model_dump(mode="json"))


async def update_pincode_zone(
    repos: Repositories, zone_id: str, changes: PincodeZoneUpdate
) -> dict[str, Any]:
    if changes.warehouse_id is not None:
        await repos.warehouses.ensure_exists(changes.warehouse_id)
    return await repos.pincode_zones.update(zone_id, changes.changes())
