import pytest
from bson import ObjectId

MEDICINE = {
    "name": "Paracetamol 500",
    "composition": "Paracetamol (500mg)",
    "manufacturer": "Micro Labs",
    "pack_size": "15 Tablet",
    "mrp": 30.5,
    "schedule": "OTC",
    "prescription_required": False,
    "gst_percent": 5,
    "hsn_code": "30049099",
}


def create(client, **overrides):
    response = client.post("/medicines", json={**MEDICINE, **overrides})
    assert response.status_code == 201, response.text
    return response.json()


def test_create_returns_201_with_id(client):
    body = create(client)

    assert ObjectId.is_valid(body["id"])
    assert body["name"] == "Paracetamol 500"
    assert body["pack_size"] == "15 Tablet"
    assert body["mrp"] == 30.5
    assert "expiry_date" not in body


def test_schedule_defaults_to_otc(client):
    payload = {k: v for k, v in MEDICINE.items() if k != "schedule"}

    response = client.post("/medicines", json=payload)

    assert response.json()["schedule"] == "OTC"


@pytest.mark.parametrize(
    "overrides",
    [
        {"mrp": 0},
        {"mrp": -5},
        {"name": ""},
        {"pack_size": ""},
        {"composition": None},
        {"schedule": "Z"},
        {"gst_percent": 7},
        {"hsn_code": "30A4"},
        {"hsn_code": "300"},
    ],
)
def test_create_rejects_invalid_data(client, overrides):
    response = client.post("/medicines", json={**MEDICINE, **overrides})

    assert response.status_code == 422


def test_same_name_and_pack_twice_is_409(client):
    create(client)

    response = client.post("/medicines", json=MEDICINE)

    assert response.status_code == 409


def test_same_name_different_pack_is_allowed(client):
    create(client)

    create(client, pack_size="10 Tablet")


def test_list_is_paginated(client):
    for i in range(3):
        create(client, name=f"Medicine {i}")

    assert len(client.get("/medicines").json()) == 3
    page = client.get("/medicines?skip=1&limit=1").json()
    assert [m["name"] for m in page] == ["Medicine 1"]


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "skip=-1"])
def test_list_rejects_bad_pagination(client, query):
    assert client.get(f"/medicines?{query}").status_code == 422


def test_get_one(client):
    created = create(client)

    response = client.get(f"/medicines/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_unknown_id_returns_404(client):
    assert client.get(f"/medicines/{ObjectId()}").status_code == 404


def test_get_malformed_id_returns_400(client):
    assert client.get("/medicines/not-an-id").status_code == 400


def test_patch_updates_only_given_fields(client):
    created = create(client)

    response = client.patch(f"/medicines/{created['id']}", json={"mrp": 42, "schedule": "H"})

    assert response.status_code == 200
    assert response.json() == {**created, "mrp": 42, "schedule": "H"}


def test_patch_with_unchanged_data_still_succeeds(client):
    created = create(client)

    response = client.patch(f"/medicines/{created['id']}", json={"mrp": created["mrp"]})

    assert response.status_code == 200


def test_patch_rejects_empty_body_and_invalid_values(client):
    created = create(client)

    assert client.patch(f"/medicines/{created['id']}", json={}).status_code == 422
    assert client.patch(f"/medicines/{created['id']}", json={"mrp": -1}).status_code == 422


def test_patch_into_existing_name_and_pack_is_409(client):
    create(client)
    other = create(client, pack_size="10 Tablet")

    response = client.patch(f"/medicines/{other['id']}", json={"pack_size": "15 Tablet"})

    assert response.status_code == 409


def test_patch_unknown_id_returns_404(client):
    assert client.patch(f"/medicines/{ObjectId()}", json={"mrp": 10}).status_code == 404


def test_delete_returns_204_then_404(client):
    created = create(client)

    assert client.delete(f"/medicines/{created['id']}").status_code == 204
    assert client.get(f"/medicines/{created['id']}").status_code == 404
    assert client.delete(f"/medicines/{created['id']}").status_code == 404
