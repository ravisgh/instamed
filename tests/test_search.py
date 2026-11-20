import pytest

from tests.test_medicines import create as create_medicine
from tests.test_pincode_zones import create as create_zone
from tests.test_stores import create as create_store


@pytest.fixture
def stocked(client):
    """Paracetamol stocked in the warehouse that serves 560038."""
    medicine = create_medicine(client, name="Paracetamol 500")
    store = create_store(client)
    create_zone(client, store["id"], pincode="560038")
    response = client.post(
        "/inventory",
        json={"medicine_id": medicine["id"], "store_id": store["id"], "quantity": 12, "price": 28},
    )
    assert response.status_code == 201
    return medicine


def search(client, pincode, name):
    return client.get("/search", params={"pincode": pincode, "medicine_name": name})


def test_finds_stock_for_pincode(client, stocked):
    response = search(client, "560038", "Paracetamol 500")

    assert response.status_code == 200
    assert response.json() == {
        "medicine_id": stocked["id"],
        "medicine_name": "Paracetamol 500",
        "price": 28,
        "quantity_available": 12,
    }


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
