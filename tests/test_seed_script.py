"""Seed CLI tests. Fake rows only; writes go to the throwaway instamed_test database."""

from datetime import date

import pytest
from pymongo import MongoClient

from app.importers.evital import clean_rows
from scripts.seed_evital import DEV_PINCODE, check_target, main, seed
from tests.conftest import TEST_DB_NAME, TEST_MONGO_URI
from tests.test_importer import row

TODAY = date(2026, 11, 21)


@pytest.mark.parametrize(
    ("uri", "db"),
    [
        ("mongodb+srv://user:pw@cluster0.example.mongodb.net", "instamed_dev"),
        ("mongodb://10.0.0.5:27017", "instamed_dev"),
        ("mongodb://localhost:27017", "instamed"),
        ("mongodb://localhost:27017", "rio_debugger"),
    ],
)
def test_guard_refuses_non_local_or_non_dev_targets(uri, db):
    with pytest.raises(SystemExit) as exc:
        check_target(uri, db)

    assert exc.value.code != 0


def test_guard_allows_local_dev_and_test():
    check_target("mongodb://localhost:27017", "instamed_dev")
    check_target("mongodb://127.0.0.1:27017", "instamed_test")


def test_main_refuses_before_reading_file(tmp_path):
    with pytest.raises(SystemExit):
        main(["--file", str(tmp_path / "missing.xlsx"), "--db", "botDB"])


def fake_clean_rows():
    rows = [
        row(),
        row(**{"Medicine Name": "Othermed Syrup", "Pack Size": "100 Ml", "Schedule": None}),
    ]
    clean, _ = clean_rows(rows, TODAY)
    return clean


def test_seed_inserts_then_is_idempotent(client):
    with MongoClient(TEST_MONGO_URI) as mongo:
        db = mongo[TEST_DB_NAME]

        first = seed(db, fake_clean_rows())
        second = seed(db, fake_clean_rows())

        assert first["medicines_inserted"] == 2
        assert first["inventory_inserted"] == 2
        assert second["medicines_inserted"] == 0
        assert second["inventory_inserted"] == 0
        assert db["medicines"].count_documents({}) == 2
        assert db["stores"].count_documents({}) == 1
        assert db["pincode_zones"].count_documents({}) == 1


def test_seeded_data_is_served_by_the_api(client):
    with MongoClient(TEST_MONGO_URI) as mongo:
        seed(mongo[TEST_DB_NAME], fake_clean_rows())

    medicines = client.get("/medicines").json()
    found = client.get(
        "/search", params={"pincode": DEV_PINCODE, "medicine_name": "testocin 500 tablet"}
    )

    assert {m["name"] for m in medicines} == {"Testocin 500 Tablet", "Othermed Syrup"}
    assert found.status_code == 200
    assert found.json()["price"] == 120.5
    assert found.json()["quantity_available"] == 3
