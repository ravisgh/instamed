import pytest
from bson import ObjectId

MEDICINE = {
    "name": "Paracetamol 500",
    "composition": "Paracetamol 500mg",
    "manufacturer": "Micro Labs",
    "price": 30.5,
    "expiry_date": "2027-06-30",
    "prescription_required": False,
}


def create(client, **overrides):
    response = client.post("/medicines", json={**MEDICINE, **overrides})
    assert response.status_code == 201, response.text
    return response.json()


def test_create_returns_201_with_id(client):
    body = create(client)

    assert ObjectId.is_valid(body["id"])
    assert body["name"] == "Paracetamol 500"
    assert body["expiry_date"] == "2027-06-30"


@pytest.mark.parametrize(
    "overrides",
    [
        {"price": 0},
        {"price": -5},
        {"name": ""},
        {"expiry_date": "30-06-2027"},
        {"composition": None},
    ],
)
def test_create_rejects_invalid_data(client, overrides):
    response = client.post("/medicines", json={**MEDICINE, **overrides})

    assert response.status_code == 422


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

    response = client.patch(f"/medicines/{created['id']}", json={"price": 42})

    assert response.status_code == 200
    assert response.json() == {**created, "price": 42}


def test_patch_with_unchanged_data_still_succeeds(client):
    created = create(client)

    response = client.patch(f"/medicines/{created['id']}", json={"price": created["price"]})

    assert response.status_code == 200


def test_patch_rejects_empty_body_and_invalid_values(client):
    created = create(client)

    assert client.patch(f"/medicines/{created['id']}", json={}).status_code == 422
    assert client.patch(f"/medicines/{created['id']}", json={"price": -1}).status_code == 422


def test_patch_unknown_id_returns_404(client):
    assert client.patch(f"/medicines/{ObjectId()}", json={"price": 10}).status_code == 404


def test_delete_returns_204_then_404(client):
    created = create(client)

    assert client.delete(f"/medicines/{created['id']}").status_code == 204
    assert client.get(f"/medicines/{created['id']}").status_code == 404
    assert client.delete(f"/medicines/{created['id']}").status_code == 404
