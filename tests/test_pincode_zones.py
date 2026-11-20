import pytest
from bson import ObjectId

from tests.test_stores import create as create_store


def create(client, warehouse_id, pincode="560038"):
    response = client.post(
        "/pincode-zones", json={"pincode": pincode, "warehouse_id": warehouse_id}
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def warehouse_id(client):
    return create_store(client)["id"]


def test_create_returns_201(client, warehouse_id):
    body = create(client, warehouse_id)

    assert body["pincode"] == "560038"
    assert body["warehouse_id"] == warehouse_id


@pytest.mark.parametrize("pincode", ["56003", "5600381", "060038", "56003A"])
def test_create_rejects_bad_pincode(client, warehouse_id, pincode):
    response = client.post(
        "/pincode-zones", json={"pincode": pincode, "warehouse_id": warehouse_id}
    )

    assert response.status_code == 422


def test_create_requires_existing_warehouse(client):
    response = client.post(
        "/pincode-zones", json={"pincode": "560038", "warehouse_id": str(ObjectId())}
    )

    assert response.status_code == 404


def test_duplicate_pincode_is_409(client, warehouse_id):
    create(client, warehouse_id)

    response = client.post(
        "/pincode-zones", json={"pincode": "560038", "warehouse_id": warehouse_id}
    )

    assert response.status_code == 409


def test_old_routes_are_gone(client):
    assert client.get("/pincode-zone").status_code == 404
    assert client.post("/pincode_zone", json={}).status_code == 404


def test_list_get_patch_delete(client, warehouse_id):
    created = create(client, warehouse_id)
    other_store = create_store(client, name="Other")["id"]

    assert client.get("/pincode-zones").json() == [created]
    assert client.get(f"/pincode-zones/{created['id']}").json() == created

    patched = client.patch(f"/pincode-zones/{created['id']}", json={"warehouse_id": other_store})
    assert patched.status_code == 200
    assert patched.json()["warehouse_id"] == other_store

    missing = client.patch(
        f"/pincode-zones/{created['id']}", json={"warehouse_id": str(ObjectId())}
    )
    assert missing.status_code == 404

    second = create(client, warehouse_id, pincode="110001")
    clash = client.patch(f"/pincode-zones/{second['id']}", json={"pincode": "560038"})
    assert clash.status_code == 409

    assert client.delete(f"/pincode-zones/{created['id']}").status_code == 204
    assert client.get(f"/pincode-zones/{created['id']}").status_code == 404
