import pytest

from app.db import get_search_index
from app.main import app
from tests.conftest import NO_AUTH, requires_es
from tests.test_medicines import create as create_medicine


class DeadIndex:
    """A search index whose every call fails, like Elasticsearch being down."""

    async def upsert(self, medicine):
        raise ConnectionError("es down")

    async def delete(self, medicine_id):
        raise ConnectionError("es down")

    async def search_ids(self, q, limit):
        raise ConnectionError("es down")


@pytest.fixture
def catalog(client):
    return {
        "paracetamol": create_medicine(
            client,
            name="Paracetamol 500 Tablet",
            composition="Paracetamol (500mg)",
            manufacturer="GlaxoSmithKline",
        ),
        "dolo": create_medicine(
            client,
            name="Dolo 650 Tablet",
            composition="Paracetamol (650mg)",
            manufacturer="Micro Labs Ltd",
        ),
        "amox": create_medicine(
            client,
            name="Mox 500 Capsule",
            composition="Amoxycillin (500mg)",
            manufacturer="Sun Pharmaceutical Industries Ltd",
            schedule="H",
            prescription_required=True,
        ),
    }


def search(client, q, **params):
    return client.get("/medicines/search", params={"q": q, **params}, headers=NO_AUTH)


@pytest.fixture
def without_es():
    app.dependency_overrides[get_search_index] = lambda: None
    yield
    app.dependency_overrides.pop(get_search_index, None)


@pytest.fixture
def dead_es():
    app.dependency_overrides[get_search_index] = lambda: DeadIndex()
    yield
    app.dependency_overrides.pop(get_search_index, None)


# --- MongoDB fallback (always runs) -------------------------------------------------


def test_fallback_matches_name_or_salt_substring(client, catalog, without_es):
    body = search(client, "paracetamol").json()

    assert body["engine"] == "mongo"
    assert [m["name"] for m in body["results"]] == ["Dolo 650 Tablet", "Paracetamol 500 Tablet"]


def test_fallback_escapes_regex_and_respects_limit(client, catalog, without_es):
    assert search(client, ".*").json()["results"] == []
    assert len(search(client, "Tablet", limit=1).json()["results"]) == 1


def test_query_validation(client, without_es):
    assert search(client, "a").status_code == 422
    assert search(client, "ab", limit=51).status_code == 422


def test_search_path_is_not_treated_as_an_id(client, without_es):
    assert search(client, "anything").status_code == 200


def test_es_outage_falls_back_and_never_breaks_writes(client, dead_es):
    created = create_medicine(client, name="Crocin Advance")  # upsert fails silently
    renamed = client.patch(f"/medicines/{created['id']}", json={"name": "Crocin Pain Relief"})

    body = search(client, "crocin").json()

    assert renamed.status_code == 200
    assert body["engine"] == "mongo"
    assert [m["name"] for m in body["results"]] == ["Crocin Pain Relief"]
    assert client.delete(f"/medicines/{created['id']}").status_code == 204


# --- Real Elasticsearch (runs when a local node is up) ------------------------------


@requires_es
def test_es_tolerates_typos(client, catalog):
    body = search(client, "paracetmol").json()

    assert body["engine"] == "elasticsearch"
    assert body["results"][0]["id"] == catalog["paracetamol"]["id"]


@requires_es
def test_es_autocompletes_and_matches_salt_and_maker(client, catalog):
    assert search(client, "dol").json()["results"][0]["id"] == catalog["dolo"]["id"]
    assert search(client, "amoxycilin").json()["results"][0]["id"] == catalog["amox"]["id"]
    assert search(client, "micro labs").json()["results"][0]["id"] == catalog["dolo"]["id"]


@requires_es
def test_es_follows_updates_and_deletes(client, catalog):
    client.patch(f"/medicines/{catalog['dolo']['id']}", json={"name": "Dolokind Plus"})
    client.delete(f"/medicines/{catalog['paracetamol']['id']}")

    assert search(client, "dolokind").json()["results"][0]["id"] == catalog["dolo"]["id"]
    ids = [m["id"] for m in search(client, "paracetamol").json()["results"]]
    assert catalog["paracetamol"]["id"] not in ids


@requires_es
def test_reindex_script_rebuilds_from_mongo(client, catalog, capsys):
    from scripts.reindex_es import main
    from tests.conftest import TEST_DB_NAME, TEST_ES_INDEX

    main(["--db", TEST_DB_NAME, "--index", TEST_ES_INDEX])

    assert "Indexed 3 of 3 medicines" in capsys.readouterr().out
    assert search(client, "paracetmol").json()["engine"] == "elasticsearch"


def test_reindex_script_refuses_remote_targets():
    from scripts.reindex_es import main

    with pytest.raises(SystemExit):
        main(["--db", "rio_debugger"])
    with pytest.raises(SystemExit):
        main(["--db", "instamed_dev", "--es-url", "https://search.example.com:9200"])


@requires_es
def test_es_ranks_whole_word_matches_above_prefixes(client, catalog):
    create_medicine(client, name="Dologel Liquid", composition="Choline salicylate (8.7%)")

    names = [m["name"] for m in search(client, "dolo").json()["results"]]

    assert names[0] == "Dolo 650 Tablet"
    assert "Dologel Liquid" in names
