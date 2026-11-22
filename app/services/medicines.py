"""Medicine writes keep the search index in sync; text search prefers Elasticsearch."""

import re
from typing import Any

from bson import ObjectId

from app.core.ids import document_to_out
from app.core.logging import get_logger
from app.models.medicine import MedicineCreate, MedicineUpdate
from app.repositories import Repositories
from app.search_engine import MedicineIndex, SearchUnavailable

log = get_logger("medicines")


async def _sync(index: MedicineIndex | None, medicine: dict[str, Any]) -> None:
    """Best effort: a search-index hiccup must never fail the write (Mongo is the truth)."""
    if index is None:
        return
    try:
        await index.upsert(medicine)
    except SearchUnavailable:
        log.info(
            "Search index down; medicine %s not indexed, run the reindex script", medicine["id"]
        )
    except Exception:
        log.warning("Could not index medicine %s; run the reindex script", medicine["id"])


async def create(repos: Repositories, index: MedicineIndex | None, body: MedicineCreate) -> dict:
    medicine = await repos.medicines.insert(body.model_dump(mode="json"))
    await _sync(index, medicine)
    return medicine


async def update(
    repos: Repositories, index: MedicineIndex | None, medicine_id: str, body: MedicineUpdate
) -> dict:
    medicine = await repos.medicines.update(medicine_id, body.changes())
    await _sync(index, medicine)
    return medicine


async def delete(repos: Repositories, index: MedicineIndex | None, medicine_id: str) -> None:
    await repos.medicines.delete(medicine_id)
    if index is not None:
        try:
            await index.delete(medicine_id)
        except Exception:
            log.warning("Could not remove medicine %s from the search index", medicine_id)


async def _mongo_search(repos: Repositories, q: str, limit: int) -> list[dict[str, Any]]:
    """Fallback: case-insensitive substring match on name or salt (no typo tolerance)."""
    pattern = {"$regex": re.escape(q.strip()), "$options": "i"}
    cursor = (
        repos.medicines.collection.find({"$or": [{"name": pattern}, {"composition": pattern}]})
        .sort("name", 1)
        .limit(limit)
    )
    return [document_to_out(doc) async for doc in cursor]


async def search(
    repos: Repositories, index: MedicineIndex | None, q: str, limit: int
) -> tuple[str, list[dict[str, Any]]]:
    """Return (engine, medicines). Elasticsearch ranks; Mongo supplies the documents."""
    if index is not None:
        try:
            ids = await index.search_ids(q, limit)
        except SearchUnavailable:
            pass  # breaker open: the failure was already logged once
        except Exception:
            log.warning("Elasticsearch search failed; falling back to MongoDB", exc_info=True)
        else:
            docs = {
                str(d["_id"]): document_to_out(d)
                async for d in repos.medicines.collection.find(
                    {"_id": {"$in": [ObjectId(i) for i in ids if ObjectId.is_valid(i)]}}
                )
            }
            return "elasticsearch", [docs[i] for i in ids if i in docs]
    return "mongo", await _mongo_search(repos, q, limit)
