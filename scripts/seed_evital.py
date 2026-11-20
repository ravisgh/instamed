"""Load clean SKUs from an eVital stock export into a LOCAL dev database.

Usage (PowerShell, from the repo root):
    python -m scripts.seed_evital --file "C:\\path\\to\\export.xlsx" --dry-run
    python -m scripts.seed_evital --file "C:\\path\\to\\export.xlsx"

Safety: refuses to run unless the Mongo host is localhost and the database is
instamed_dev or instamed_test. It never reads .env. The export file stays where it is;
nothing from it is written into the repository.
"""

import argparse
import sys
from collections import Counter
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from pymongo import MongoClient, ReturnDocument, UpdateOne
from pymongo.database import Database

from app.importers.evital import CleanRow, clean_rows, read_rows

ALLOWED_HOSTS = {"localhost", "127.0.0.1"}
ALLOWED_DBS = {"instamed_dev", "instamed_test"}

DEV_PINCODE = "201014"  # Indirapuram, Ghaziabad
DEV_STORE = {
    "name": "InstaMed Indirapuram (dev)",
    "latitude": 28.6460,
    "longitude": 77.3695,
    "contact_number": "+919999999999",  # placeholder
    "email": "indirapuram.dev@instamed.example",  # placeholder
    "opening_hours": "08:00-23:00",
}


def check_target(mongo_uri: str, db_name: str) -> None:
    """Exit unless we are pointed at a local dev/test database."""
    host = urlparse(mongo_uri).hostname
    if host not in ALLOWED_HOSTS or db_name not in ALLOWED_DBS:
        sys.exit(
            f"Refusing to seed host={host!r} db={db_name!r}. "
            f"Allowed hosts: {sorted(ALLOWED_HOSTS)}, dbs: {sorted(ALLOWED_DBS)}."
        )


def _ensure_indexes(db: Database) -> None:
    # Same indexes the API creates in app/db.py, so upserts can rely on them.
    db["pincode_zones"].create_index("pincode", unique=True)
    db["medicines"].create_index([("name", 1), ("pack_size", 1)], unique=True)
    db["inventory"].create_index([("store_id", 1), ("medicine_id", 1)], unique=True)


def seed(db: Database, rows: Sequence[CleanRow]) -> dict[str, int]:
    """Upsert the dev store, its pincode zone, medicines and inventory. Safe to re-run."""
    _ensure_indexes(db)

    store = db["stores"].find_one_and_update(
        {"name": DEV_STORE["name"]},
        {"$set": DEV_STORE},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    store_id = str(store["_id"])
    db["pincode_zones"].update_one(
        {"pincode": DEV_PINCODE}, {"$set": {"warehouse_id": store_id}}, upsert=True
    )

    medicine_ops = [
        UpdateOne(
            {"name": r.medicine.name, "pack_size": r.medicine.pack_size},
            {"$set": r.medicine.model_dump(mode="json")},
            upsert=True,
        )
        for r in rows
    ]
    medicines = db["medicines"].bulk_write(medicine_ops) if medicine_ops else None

    ids = {
        (doc["name"], doc["pack_size"]): str(doc["_id"])
        for doc in db["medicines"].find({}, {"name": 1, "pack_size": 1})
    }
    inventory_ops = [
        UpdateOne(
            {"store_id": store_id, "medicine_id": ids[(r.medicine.name, r.medicine.pack_size)]},
            {
                "$set": {
                    "quantity": r.quantity,
                    "price": r.price,
                    "earliest_expiry": r.earliest_expiry.isoformat(),
                    "batch_count": r.batch_count,
                    "location": r.location,
                }
            },
            upsert=True,
        )
        for r in rows
    ]
    inventory = db["inventory"].bulk_write(inventory_ops) if inventory_ops else None

    return {
        "medicines_inserted": medicines.upserted_count if medicines else 0,
        "medicines_updated": medicines.modified_count if medicines else 0,
        "inventory_inserted": inventory.upserted_count if inventory else 0,
        "inventory_updated": inventory.modified_count if inventory else 0,
    }


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--file", required=True, type=Path, help="eVital export (.xlsx)")
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017")
    parser.add_argument("--db", default="instamed_dev")
    parser.add_argument("--dry-run", action="store_true", help="clean and report, write nothing")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="drop medicines/stores/inventory/pincode_zones in the target db first",
    )
    args = parser.parse_args(argv)

    check_target(args.mongo_uri, args.db)  # before touching the file or the database
    if not args.file.is_file():
        sys.exit(f"File not found: {args.file}")

    clean, dropped = clean_rows(read_rows(args.file), date.today())
    print(f"Rows read: {len(clean) + len(dropped)}")
    print(f"Clean:     {len(clean)}")
    print(f"Dropped:   {len(dropped)}")
    for reason, count in Counter(d.reason for d in dropped).most_common():
        print(f"  {count:6}  {reason}")

    if args.dry_run:
        print("Dry run: nothing written.")
        return

    with MongoClient(args.mongo_uri, serverSelectionTimeoutMS=3000) as mongo:
        db = mongo[args.db]
        if args.reset:
            for name in ("medicines", "stores", "inventory", "pincode_zones"):
                db.drop_collection(name)
            print(f"Reset: dropped app collections in {args.db}")
        report = seed(db, clean)

    print(f"Wrote to {args.db}:")
    for key, value in report.items():
        print(f"  {key:20} {value}")


if __name__ == "__main__":
    main()
