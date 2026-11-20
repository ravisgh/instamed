import pytest

from tests.conftest import NO_AUTH
from tests.test_medicines import create as create_medicine
from tests.test_pincode_zones import create as create_zone
from tests.test_stores import create as create_store


def stock(client, medicine_id, store_id, quantity, price):
    response = client.post(
        "/inventory",
        json={
            "medicine_id": medicine_id,
            "store_id": store_id,
            "quantity": quantity,
            "price": price,
        },
    )
    assert response.status_code == 201, response.text


@pytest.fixture
def stocked(client):
    """Paracetamol 500 in two pack sizes, stocked in the warehouse that serves 560038."""
    strip_15 = create_medicine(client, name="Paracetamol 500", pack_size="15 Tablet")
    strip_10 = create_medicine(client, name="Paracetamol 500", pack_size="10 Tablet", mrp=21)
    store = create_store(client)
    create_zone(client, store["id"], pincode="560038")
    stock(client, strip_15["id"], store["id"], quantity=12, price=28)
    stock(client, strip_10["id"], store["id"], quantity=4, price=20)
    return {"store": store, "strip_15": strip_15, "strip_10": strip_10}


def search(client, pincode, name):
    return client.get(
        "/search", params={"pincode": pincode, "medicine_name": name}, headers=NO_AUTH
    )


def test_returns_every_stocked_pack_size(client, stocked):
    response = search(client, "560038", "Paracetamol 500")

    assert response.status_code == 200
    body = response.json()
    assert body["pincode"] == "560038"
    assert body["store_id"] == stocked["store"]["id"]
    assert body["results"] == [
        {
            "medicine_id": stocked["strip_10"]["id"],
            "name": "Paracetamol 500",
            "pack_size": "10 Tablet",
            "mrp": 21.0,
            "price": 20.0,
            "quantity_available": 4,
            "prescription_required": False,
        },
        {
            "medicine_id": stocked["strip_15"]["id"],
            "name": "Paracetamol 500",
            "pack_size": "15 Tablet",
            "mrp": 30.5,
            "price": 28.0,
            "quantity_available": 12,
            "prescription_required": False,
        },
    ]


def test_out_of_stock_packs_are_hidden(client, stocked):
    item = client.get("/inventory").json()[1]  # the 10-tablet row
    client.patch(f"/inventory/{item['id']}", json={"quantity": 0})

    results = search(client, "560038", "Paracetamol 500").json()["results"]

    assert [r["pack_size"] for r in results] == ["15 Tablet"]


@pytest.mark.parametrize("name", ["paracetamol 500", "PARACETAMOL 500", "  Paracetamol 500 "])
def test_name_match_is_case_insensitive_and_trimmed(client, stocked, name):
    assert search(client, "560038", name).status_code == 200


def test_name_is_exact_not_partial_or_regex(client, stocked):
    assert search(client, "560038", "Paracetamol").status_code == 404
    assert search(client, "560038", ".*").status_code == 404


def test_unserviceable_pincode_is_404(client, stocked):
    response = search(client, "110001", "Paracetamol 500")

    assert response.status_code == 404
    assert response.json()["detail"] == "Pincode not serviceable"


def test_unknown_medicine_is_404(client, stocked):
    response = search(client, "560038", "Crocin")

    assert response.status_code == 404
    assert response.json()["detail"] == "Medicine not found"


def test_medicine_not_stocked_in_area_is_404(client, stocked):
    create_medicine(client, name="Crocin")

    response = search(client, "560038", "Crocin")

    assert response.status_code == 404
    assert response.json()["detail"] == "Medicine not available in your area"


@pytest.mark.parametrize("pincode", ["5600", "abcdef", "060038"])
def test_invalid_pincode_is_422(client, pincode):
    assert search(client, pincode, "Paracetamol 500").status_code == 422
