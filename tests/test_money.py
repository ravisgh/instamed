from decimal import Decimal

import pytest

from app.core.money import line_total, order_total, to_money
from tests.test_inventory import create as create_inventory
from tests.test_medicines import MEDICINE


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0.1, Decimal("0.10")), (2.675, Decimal("2.68")), (10, Decimal("10.00"))],
)
def test_to_money_rounds_half_up_from_the_decimal_text(value, expected):
    assert to_money(value) == expected


def test_line_and_order_totals_are_exact():
    lines = [line_total(0.1, 3), line_total(0.2, 1)]

    assert lines == [0.3, 0.2]
    assert order_total(lines) == 0.5
    assert order_total([0.1, 0.2]) == 0.3  # 0.1 + 0.2 != 0.3 in plain floats


@pytest.mark.parametrize("mrp", [10.005, 0.001, 99.999])
def test_medicine_mrp_allows_at_most_two_decimals(client, mrp):
    assert client.post("/medicines", json={**MEDICINE, "mrp": mrp}).status_code == 422


def test_two_decimal_prices_are_accepted(client):
    assert client.post("/medicines", json={**MEDICINE, "mrp": 12.34}).status_code == 201


def test_inventory_price_allows_at_most_two_decimals(client):
    medicine = client.post("/medicines", json=MEDICINE).json()
    store = client.post(
        "/stores",
        json={
            "name": "S",
            "latitude": 1,
            "longitude": 1,
            "contact_number": "+919876543210",
            "email": "s@instamed.example",
            "opening_hours": "24x7",
        },
    ).json()
    refs = {"medicine_id": medicine["id"], "store_id": store["id"]}

    bad = client.post("/inventory", json={**refs, "quantity": 1, "price": 1.234})
    good = create_inventory(client, refs, price=1.23)

    assert bad.status_code == 422
    assert good["price"] == 1.23
