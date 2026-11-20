"""Elasticsearch-backed medicine search (optional).

MongoDB stays the source of truth. Elasticsearch holds a searchable copy of each
medicine (name, salt, manufacturer) and only answers "which ids match `q`, best first".
If ELASTICSEARCH_URL is unset, or Elasticsearch is down, callers fall back to Mongo.
"""

from typing import Any

from elasticsearch import AsyncElasticsearch, helpers

INDEX_SETTINGS: dict[str, Any] = {
    "analysis": {
        "filter": {
            "autocomplete_filter": {"type": "edge_ngram", "min_gram": 2, "max_gram": 20},
        },
        "analyzer": {
            "autocomplete": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": ["lowercase", "asciifolding", "autocomplete_filter"],
            },
            "folded": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": ["lowercase", "asciifolding"],
            },
        },
    }
}

INDEX_MAPPINGS: dict[str, Any] = {
    "properties": {
        "name": {
            "type": "text",
            "analyzer": "folded",
            "fields": {
                "autocomplete": {
                    "type": "text",
                    "analyzer": "autocomplete",
                    "search_analyzer": "folded",
                },
                "raw": {"type": "keyword"},
            },
        },
        "composition": {"type": "text", "analyzer": "folded"},
        "manufacturer": {"type": "text", "analyzer": "folded"},
        "pack_size": {"type": "keyword"},
        "schedule": {"type": "keyword"},
    }
}

SEARCH_FIELDS = ["name", "pack_size", "composition", "manufacturer", "schedule"]


def to_search_doc(medicine: dict[str, Any]) -> dict[str, Any]:
    return {field: medicine.get(field) for field in SEARCH_FIELDS}


class MedicineIndex:
    def __init__(self, client: AsyncElasticsearch, index: str, refresh: bool = False):
        self.client = client
        self.index = index
        # refresh=True makes writes visible to search immediately (tests); slower.
        self.refresh = "true" if refresh else "false"

    async def ensure_index(self) -> None:
        if not await self.client.indices.exists(index=self.index):
            await self.client.indices.create(
                index=self.index, settings=INDEX_SETTINGS, mappings=INDEX_MAPPINGS
            )

    async def upsert(self, medicine: dict[str, Any]) -> None:
        await self.client.index(
            index=self.index,
            id=medicine["id"],
            document=to_search_doc(medicine),
            refresh=self.refresh,
        )

    async def delete(self, medicine_id: str) -> None:
        await self.client.delete(
            index=self.index, id=medicine_id, refresh=self.refresh, ignore_status=404
        )

    async def search_ids(self, q: str, limit: int) -> list[str]:
        """Ids of the best matches: typo-tolerant on names, also matches salts and makers."""
        response = await self.client.search(
            index=self.index,
            size=limit,
            query={
                "bool": {
                    "should": [
                        # Exact full name, then whole words ("dolo" -> "Dolo 650"),
                        # then prefixes ("dolo" -> "Dologel"), then fuzzy/salt/maker.
                        {"match": {"name.raw": {"query": q, "boost": 10}}},
                        {"match": {"name": {"query": q, "operator": "and", "boost": 6}}},
                        {"match_phrase_prefix": {"name": {"query": q, "boost": 2}}},
                        {
                            "multi_match": {
                                "query": q,
                                "fields": [
                                    "name^3",
                                    "name.autocomplete^2",
                                    "composition^1.5",
                                    "manufacturer",
                                ],
                                "fuzziness": "AUTO",
                                "prefix_length": 1,
                            }
                        },
                    ],
                    "minimum_should_match": 1,
                }
            },
            source=False,
        )
        return [hit["_id"] for hit in response["hits"]["hits"]]

    async def reindex(self, medicines: list[dict[str, Any]]) -> int:
        """Drop and rebuild the index from the given medicines. Returns the count indexed."""
        await self.client.indices.delete(index=self.index, ignore_unavailable=True)
        await self.ensure_index()
        actions = (
            {"_index": self.index, "_id": m["id"], "_source": to_search_doc(m)} for m in medicines
        )
        indexed, _ = await helpers.async_bulk(self.client, actions, refresh="true")
        return indexed

    async def close(self) -> None:
        await self.client.close()
