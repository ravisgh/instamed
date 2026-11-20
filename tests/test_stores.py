import pytest
from bson import ObjectId

STORE = {
    "name": "InstaMed Indiranagar",
    "latitude": 12.9784,
    "longitude": 77.6408,
    "contact_number": "+919876543210",
    "email": "indiranagar@instamed.example",
    "opening_hours": "08:00-22:00",
}


def create(client, **overrides):
    response = client.post("/stores", json={**STORE, **overrides})
    assert response.status_code == 201, response.text
    return response.json()


def test_create_returns_201_with_id(client):
    body = create(client)

    assert ObjectId.is_valid(body["id"])
    assert body["email"] == STORE["email"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"email": "not-an-email"},
        {"latitude": 91},
        {"longitude": -181},
        {"contact_number": "12345"},
        {"contact_number": "98765abcde"},
        {"name": ""},
    ],
)
def test_create_rejects_invalid_data(client, overrides):
    assert client.post("/stores", json={**STORE, **overrides}).status_code == 422


def test_list_is_paginated(client):
    for i in range(3):
        create(client, name=f"Store {i}")

    page = client.get("/stores?skip=2&limit=5").json()

    assert [s["name"] for s in page] == ["Store 2"]


def test_get_one_and_errors(client):
    created = create(client)

    assert client.get(f"/stores/{created['id']}").json() == created
    assert client.get(f"/stores/{ObjectId()}").status_code == 404
    assert client.get("/stores/bad").status_code == 400


def test_patch_updates_only_given_fields(client):
    created = create(client)

    response = client.patch(f"/stores/{created['id']}", json={"opening_hours": "24x7"})

    assert response.status_code == 200
    assert response.json() == {**created, "opening_hours": "24x7"}
    assert client.patch(f"/stores/{created['id']}", json={"email": "x"}).status_code == 422
    assert client.patch(f"/stores/{ObjectId()}", json={"name": "X"}).status_code == 404


def test_delete_returns_204_then_404(client):
    created = create(client)

    assert client.delete(f"/stores/{created['id']}").status_code == 204
    assert client.delete(f"/stores/{created['id']}").status_code == 404
