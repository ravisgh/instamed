"""Elasticsearch-backed medicine search (optional).

MongoDB stays the source of truth. Elasticsearch holds a searchable copy of each
medicine (name, salt, manufacturer) and only answers "which ids match `q`, best first".
If ELASTICSEARCH_URL is unset, or Elasticsearch is down, callers fall back to Mongo.

Falling back has to be fast. The client does not retry, searches get a short timeout,
and after a failure a circuit breaker skips Elasticsearch for `cooldown` seconds, so
only one request pays for an outage. The first call after the cooldown probes again.
"""

import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from elasticsearch import AsyncElasticsearch, helpers

from app.core.logging import get_logger

log = get_logger("search")
T = TypeVar("T")


class SearchUnavailable(Exception):
    """Elasticsearch failed recently; skipped without a network call (breaker open)."""


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
    # For the app's client: an unreachable node must fail once, not retry in a loop.
    CLIENT_OPTIONS: dict[str, Any] = {
        "request_timeout": 5,
        "max_retries": 0,
        "retry_on_timeout": False,
    }

    def __init__(
        self,
        client: AsyncElasticsearch,
        index: str,
        refresh: bool = False,
        search_timeout: float = 1.0,
        cooldown: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.client = client
        self.index = index
        # refresh=True makes writes visible to search immediately (tests); slower.
        self.refresh = "true" if refresh else "false"
        self.search_timeout = search_timeout
        self.cooldown = cooldown
        self._clock = clock
        self._down_until: float | None = None

    @property
    def available(self) -> bool:
        """False while the breaker is open (a recent failure, cooldown not over yet)."""
        return self._down_until is None or self._clock() >= self._down_until

    async def _guarded(self, call: Callable[[], Awaitable[T]]) -> T:
        if not self.available:
            raise SearchUnavailable(f"Elasticsearch skipped until cooldown ends ({self.index})")
        try:
            result = await call()
        except Exception:
            if self._down_until is None:
                log.warning(
                    "Elasticsearch unavailable; using MongoDB for %ss before retrying",
                    self.cooldown,
                )
            self._down_until = self._clock() + self.cooldown
            raise
        if self._down_until is not None:
            log.info("Elasticsearch is back")
            self._down_until = None
        return result

    async def ensure_index(self) -> None:
        async def call() -> None:
            if not await self.client.indices.exists(index=self.index):
                await self.client.indices.create(
                    index=self.index, settings=INDEX_SETTINGS, mappings=INDEX_MAPPINGS
                )

        await self._guarded(call)

    async def upsert(self, medicine: dict[str, Any]) -> None:
        await self._guarded(
            lambda: self.client.index(
                index=self.index,
                id=medicine["id"],
                document=to_search_doc(medicine),
                refresh=self.refresh,
            )
        )

    async def delete(self, medicine_id: str) -> None:
        await self._guarded(
            lambda: self.client.delete(
                index=self.index, id=medicine_id, refresh=self.refresh, ignore_status=404
            )
        )

    async def search_ids(self, q: str, limit: int) -> list[str]:
        """Ids of the best matches: typo-tolerant on names, also matches salts and makers."""
        response = await self._guarded(lambda: self._search(q, limit))
        return [hit["_id"] for hit in response["hits"]["hits"]]

    async def _search(self, q: str, limit: int) -> Any:
        return await self.client.options(request_timeout=self.search_timeout).search(
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
