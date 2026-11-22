"""When Elasticsearch is down, search must fall back to MongoDB fast, not after retries."""

import asyncio
import time

import pytest
from elasticsearch import AsyncElasticsearch

from app.search_engine import MedicineIndex, SearchUnavailable


class FakeClient:
    """Stands in for AsyncElasticsearch; counts calls and fails while `down` is set."""

    def __init__(self):
        self.down = False
        self.calls = 0
        self.timeouts: list[float | None] = []

    def options(self, request_timeout=None):
        self.timeouts.append(request_timeout)
        return self

    async def search(self, **kwargs):
        self.calls += 1
        if self.down:
            raise ConnectionError("es down")
        return {"hits": {"hits": [{"_id": "m1"}]}}

    async def index(self, **kwargs):
        self.calls += 1
        if self.down:
            raise ConnectionError("es down")


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def make_index(client, clock):
    return MedicineIndex(client, "medicines", search_timeout=1.0, cooldown=30.0, clock=clock)


def test_search_uses_a_short_per_request_timeout():
    client = FakeClient()
    index = make_index(client, Clock())

    assert asyncio.run(index.search_ids("dolo", 5)) == ["m1"]
    assert client.timeouts == [1.0]


def test_a_failure_skips_elasticsearch_until_the_cooldown_ends():
    client, clock = FakeClient(), Clock()
    index = make_index(client, clock)
    client.down = True

    with pytest.raises(ConnectionError):
        asyncio.run(index.search_ids("dolo", 5))
    assert client.calls == 1

    # Within the cooldown: no network call at all, callers fall back straight away.
    clock.now += 29
    with pytest.raises(SearchUnavailable):
        asyncio.run(index.search_ids("dolo", 5))
    with pytest.raises(SearchUnavailable):
        asyncio.run(index.upsert({"id": "m1", "name": "Dolo 650"}))
    assert client.calls == 1
    assert not index.available

    # After the cooldown one request probes Elasticsearch again; success closes the breaker.
    clock.now += 2
    client.down = False
    assert asyncio.run(index.search_ids("dolo", 5)) == ["m1"]
    assert client.calls == 2
    assert index.available


def test_a_failed_probe_reopens_the_breaker():
    client, clock = FakeClient(), Clock()
    index = make_index(client, clock)
    client.down = True

    with pytest.raises(ConnectionError):
        asyncio.run(index.search_ids("dolo", 5))
    clock.now += 31
    with pytest.raises(ConnectionError):
        asyncio.run(index.search_ids("dolo", 5))
    clock.now += 10
    with pytest.raises(SearchUnavailable):
        asyncio.run(index.search_ids("dolo", 5))
    assert client.calls == 2


def test_unreachable_node_fails_fast_with_the_app_client_settings():
    """A real client pointed at a closed port: one quick failure, then instant skips."""

    async def run():
        index = MedicineIndex(
            AsyncElasticsearch("http://127.0.0.1:9", **MedicineIndex.CLIENT_OPTIONS),
            "medicines",
            search_timeout=1.0,
        )
        try:
            started = time.perf_counter()
            with pytest.raises(Exception):
                await index.search_ids("dolo", 5)
            first = time.perf_counter() - started

            started = time.perf_counter()
            with pytest.raises(SearchUnavailable):
                await index.search_ids("dolo", 5)
            second = time.perf_counter() - started
        finally:
            await index.close()
        return first, second

    first, second = asyncio.run(run())
    assert first < 3.0  # was ~8s with the client's default retries
    assert second < 0.05
