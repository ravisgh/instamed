import pytest
from bson import ObjectId

from tests.test_medicines import create as create_medicine
from tests.test_stores import create as create_store


@pytest.fixture
def refs(client):
    return {
        "medicine_id": create_medicine(client)["id"],
        "store_id": create_store(client)["id"],
    }


def create(client, refs, **overrides):
    response = client.post("/inventory", json={**refs, "quantity": 50, "price": 28, **overrides})
    assert response.status_code == 201, response.text
    return response.json()


def test_create_returns_201(client, refs):
    body = create(client, refs)

    assert ObjectId.is_valid(body["id"])
    assert body["quantity"] == 50


@pytest.mark.parametrize(
    "overrides",
    [{"quantity": -1}, {"price": 0}, {"medicine_id": "bad"}, {"store_id": "bad"}],
)
def test_create_rejects_invalid_data(client, refs, overrides):
    payload = {**refs, "quantity": 5, "price": 10, **overrides}

    assert client.post("/inventory", json=payload).status_code == 422


@pytest.mark.parametrize("missing", ["medicine_id", "store_id"])
def test_create_requires_existing_medicine_and_store(client, refs, missing):
    payload = {**refs, missing: str(ObjectId()), "quantity": 5, "price": 10}

    response = client.post("/inventory", json=payload)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_same_medicine_in_same_store_twice_is_409(client, refs):
    create(client, refs)

    response = client.post("/inventory", json={**refs, "quantity": 1, "price": 1})

    assert response.status_code == 409


def test_list_get_patch_delete(client, refs):
    created = create(client, refs)

    assert client.get("/inventory?limit=1").json() == [created]
    assert client.get(f"/inventory/{created['id']}").json() == created

    patched = client.patch(f"/inventory/{created['id']}", json={"quantity": 0})
    assert patched.status_code == 200
    assert patched.json()["quantity"] == 0

    assert client.patch(f"/inventory/{created['id']}", json={"price": -2}).status_code == 422
    assert client.delete(f"/inventory/{created['id']}").status_code == 204
    assert client.get(f"/inventory/{created['id']}").status_code == 404
    assert client.get("/inventory/bad").status_code == 400
