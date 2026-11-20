"""Rebuild the Elasticsearch medicine index from a LOCAL MongoDB database.

Usage (PowerShell, from the repo root):
    python -m scripts.reindex_es                      # instamed_dev -> index "medicines"
    python -m scripts.reindex_es --index medicines_v2

Both ends must be local: Mongo localhost + instamed_dev/instamed_test, and an
Elasticsearch URL on localhost.
"""

import argparse
import asyncio
import sys
from collections.abc import Sequence
from urllib.parse import urlparse

from elasticsearch import AsyncElasticsearch
from pymongo import MongoClient

from app.core.ids import document_to_out
from app.search_engine import MedicineIndex
from scripts.safety import ALLOWED_HOSTS, check_target


async def _rebuild(es_url: str, index_name: str, medicines: list[dict]) -> int:
    index = MedicineIndex(AsyncElasticsearch(es_url, request_timeout=60), index_name)
    try:
        return await index.reindex(medicines)
    finally:
        await index.close()


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017")
    parser.add_argument("--db", default="instamed_dev")
    parser.add_argument("--es-url", default="http://127.0.0.1:9200")
    parser.add_argument("--index", default="medicines")
    args = parser.parse_args(argv)

    check_target(args.mongo_uri, args.db)
    if urlparse(args.es_url).hostname not in ALLOWED_HOSTS:
        sys.exit(f"Refusing non-local Elasticsearch {args.es_url!r}")

    with MongoClient(args.mongo_uri, serverSelectionTimeoutMS=3000) as mongo:
        medicines = [document_to_out(doc) for doc in mongo[args.db]["medicines"].find()]
    indexed = asyncio.run(_rebuild(args.es_url, args.index, medicines))
    print(f"Indexed {indexed} of {len(medicines)} medicines into {args.index!r}")


if __name__ == "__main__":
    main()
