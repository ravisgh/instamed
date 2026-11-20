import pytest
from bson import ObjectId

from tests.conftest import NO_AUTH, create_user
from tests.test_medicines import create as create_medicine
from tests.test_pincode_zones import create as create_zone
from tests.test_prescriptions import upload
from tests.test_stores import create as create_store

PINCODE = "560038"


@pytest.fixture
def shop(client):
    """One store serving 560038 with an OTC and a prescription (H) medicine in stock."""
    store = create_store(client)
    create_zone(client, store["id"], pincode=PINCODE)
    otc = create_medicine(client, name="Paracetamol 500")
    scarce = create_medicine(client, name="Cetirizine 10")
    rx = create_medicine(client, name="Amoxicillin 500", schedule="H", prescription_required=True)
    for medicine, quantity, price in ((otc, 10, 28.0), (scarce, 1, 18.0), (rx, 3, 95.5)):
        response = client.post(
            "/inventory",
            json={
                "medicine_id": medicine["id"],
                "store_id": store["id"],
                "quantity": quantity,
                "price": price,
            },
        )
        assert response.status_code == 201
    return {"store": store, "otc": otc, "scarce": scarce, "rx": rx}


def stock_of(client, medicine_id):
    rows = client.get("/inventory").json()
    return next(r["quantity"] for r in rows if r["medicine_id"] == medicine_id)


def place(client, user, items, **extra):
    return client.post(
        "/orders", json={"pincode": PINCODE, "items": items, **extra}, headers=user["headers"]
    )


def test_place_order_reserves_stock_and_prices_lines(client, shop, customer):
    response = place(client, customer, [{"medicine_id": shop["otc"]["id"], "quantity": 3}])

    assert response.status_code == 201
    order = response.json()
    assert order["status"] == "placed"
    assert order["user_id"] == customer["id"]
    assert order["store_id"] == shop["store"]["id"]
    assert order["items"] == [
        {
            "medicine_id": shop["otc"]["id"],
            "name": "Paracetamol 500",
            "pack_size": "15 Tablet",
            "quantity": 3,
            "unit_price": 28.0,
            "line_total": 84.0,
        }
    ]
    assert order["total"] == 84.0
    assert stock_of(client, shop["otc"]["id"]) == 7


def test_insufficient_stock_is_409_and_rolls_back(client, shop, customer):
    response = place(
        client,
        customer,
        [
            {"medicine_id": shop["otc"]["id"], "quantity": 2},
            {"medicine_id": shop["scarce"]["id"], "quantity": 5},  # only 1 in stock
        ],
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Insufficient stock for Cetirizine 10"
    assert stock_of(client, shop["otc"]["id"]) == 10  # first line was released again
    assert stock_of(client, shop["scarce"]["id"]) == 1


def test_cannot_oversell_across_orders(client, shop, customer):
    first = place(client, customer, [{"medicine_id": shop["otc"]["id"], "quantity": 10}])
    second = place(client, customer, [{"medicine_id": shop["otc"]["id"], "quantity": 1}])

    assert first.status_code == 201
    assert second.status_code == 409
    assert "Insufficient stock" in second.json()["detail"]
    assert stock_of(client, shop["otc"]["id"]) == 0


def test_prescription_medicine_needs_approved_prescription(client, shop, customer, pharmacist):
    items = [{"medicine_id": shop["rx"]["id"], "quantity": 1}]

    assert place(client, customer, items).status_code == 400

    rx = upload(client, customer).json()
    assert place(client, customer, items, prescription_id=rx["id"]).status_code == 400  # pending

    client.patch(
        f"/prescriptions/{rx['id']}/review",
        json={"status": "approved"},
        headers=pharmacist["headers"],
    )
    ok = place(client, customer, items, prescription_id=rx["id"])
    assert ok.status_code == 201
    assert ok.json()["prescription_id"] == rx["id"]


def test_someone_elses_prescription_is_rejected(client, shop, customer, pharmacist):
    other = create_user("customer", email="other@example.com")
    rx = upload(client, other).json()
    client.patch(
        f"/prescriptions/{rx['id']}/review",
        json={"status": "approved"},
        headers=pharmacist["headers"],
    )

    response = place(
        client,
        customer,
        [{"medicine_id": shop["rx"]["id"], "quantity": 1}],
        prescription_id=rx["id"],
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    ("items", "pincode", "status"),
    [
        ([], PINCODE, 422),
        ([{"medicine_id": "bad", "quantity": 1}], PINCODE, 422),
        ([{"medicine_id": str(ObjectId()), "quantity": 0}], PINCODE, 422),
        ([{"medicine_id": str(ObjectId()), "quantity": 1}], PINCODE, 404),
        ([{"medicine_id": str(ObjectId()), "quantity": 1}], "110001", 404),
    ],
)
def test_order_validation(client, shop, customer, items, pincode, status):
    response = client.post(
        "/orders", json={"pincode": pincode, "items": items}, headers=customer["headers"]
    )

    assert response.status_code == status


def test_duplicate_lines_are_422(client, shop, customer):
    line = {"medicine_id": shop["otc"]["id"], "quantity": 1}

    assert place(client, customer, [line, line]).status_code == 422


def test_orders_need_login(client, shop):
    response = client.post(
        "/orders",
        json={"pincode": PINCODE, "items": [{"medicine_id": shop["otc"]["id"], "quantity": 1}]},
        headers=NO_AUTH,
    )

    assert response.status_code == 401


def test_customers_see_only_their_orders(client, shop, customer, pharmacist):
    mine = place(client, customer, [{"medicine_id": shop["otc"]["id"], "quantity": 1}]).json()
    other = create_user("customer", email="other@example.com")
    theirs = place(client, other, [{"medicine_id": shop["otc"]["id"], "quantity": 1}]).json()

    assert [o["id"] for o in client.get("/orders", headers=customer["headers"]).json()] == [
        mine["id"]
    ]
    assert len(client.get("/orders", headers=pharmacist["headers"]).json()) == 2
    assert client.get(f"/orders/{theirs['id']}", headers=customer["headers"]).status_code == 404
    assert client.get(f"/orders/{theirs['id']}", headers=pharmacist["headers"]).status_code == 200


def test_cancel_restocks(client, shop, customer):
    order = place(client, customer, [{"medicine_id": shop["otc"]["id"], "quantity": 4}]).json()

    response = client.post(f"/orders/{order['id']}/cancel", headers=customer["headers"])

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert stock_of(client, shop["otc"]["id"]) == 10
    again = client.post(f"/orders/{order['id']}/cancel", headers=customer["headers"])
    assert again.status_code == 409


def test_status_flow_is_enforced(client, shop, customer, pharmacist):
    order = place(client, customer, [{"medicine_id": shop["otc"]["id"], "quantity": 1}]).json()
    url = f"/orders/{order['id']}/status"

    def move(status, user=pharmacist):
        return client.patch(url, json={"status": status}, headers=user["headers"])

    assert move("delivered").status_code == 409  # cannot skip steps
    assert move("confirmed", user=customer).status_code == 403
    assert move("confirmed").json()["status"] == "confirmed"
    assert move("dispatched").json()["status"] == "dispatched"
    # Once dispatched the customer can no longer cancel.
    assert (
        client.post(f"/orders/{order['id']}/cancel", headers=customer["headers"]).status_code == 409
    )
    delivered = move("delivered").json()
    assert delivered["status"] == "delivered"
    assert [h["status"] for h in delivered["history"]] == [
        "placed",
        "confirmed",
        "dispatched",
        "delivered",
    ]
