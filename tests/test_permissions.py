"""Who may do what. Reads are public; writes need staff roles."""

import pytest

from tests.conftest import NO_AUTH
from tests.test_medicines import MEDICINE
from tests.test_stores import STORE


@pytest.mark.parametrize("path", ["/medicines", "/stores", "/inventory", "/pincode-zones"])
def test_reads_are_public(client, path):
    assert client.get(path, headers=NO_AUTH).status_code == 200


def test_anonymous_writes_are_401(client):
    assert client.post("/medicines", json=MEDICINE, headers=NO_AUTH).status_code == 401
    assert client.post("/stores", json=STORE, headers=NO_AUTH).status_code == 401


def test_customer_cannot_write_catalog(client, customer):
    response = client.post("/medicines", json=MEDICINE, headers=customer["headers"])

    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"


def test_pharmacist_manages_medicines_and_inventory(client, pharmacist):
    medicine = client.post("/medicines", json=MEDICINE, headers=pharmacist["headers"])
    store = client.post("/stores", json=STORE)  # admin
    stock = client.post(
        "/inventory",
        json={
            "medicine_id": medicine.json()["id"],
            "store_id": store.json()["id"],
            "quantity": 5,
            "price": 30,
        },
        headers=pharmacist["headers"],
    )

    assert medicine.status_code == 201
    assert stock.status_code == 201


def test_pharmacist_cannot_manage_stores_or_zones(client, pharmacist):
    assert client.post("/stores", json=STORE, headers=pharmacist["headers"]).status_code == 403
    zone = {"pincode": "560038", "warehouse_id": "0" * 24}
    assert (
        client.post("/pincode-zones", json=zone, headers=pharmacist["headers"]).status_code == 403
    )


def test_debug_endpoint_is_gone(client):
    assert client.get("/test-db").status_code == 404
