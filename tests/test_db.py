from pymongo import MongoClient

from tests.conftest import TEST_DB_NAME, TEST_MONGO_URI


def test_lifespan_opens_the_test_database(client):
    assert client.app.state.db.name == "instamed_test"


def test_lifespan_creates_unique_indexes(client):
    with MongoClient(TEST_MONGO_URI) as mongo:
        db = mongo[TEST_DB_NAME]
        unique = {
            name: [i["key"] for i in db[name].list_indexes() if i.get("unique")]
            for name in ("pincode_zones", "medicines", "inventory", "users")
        }

    assert unique["pincode_zones"] == [{"pincode": 1}]
    assert unique["medicines"] == [{"name": 1, "pack_size": 1}]
    assert unique["inventory"] == [{"store_id": 1, "medicine_id": 1}]
    assert unique["users"] == [{"email": 1}]
