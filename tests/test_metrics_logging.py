import json
import logging

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.logging import JsonFormatter
from app.main import create_app
from tests.conftest import NO_AUTH
from tests.test_orders import PINCODE, shop  # noqa: F401  (fixture)


def test_json_formatter_emits_one_json_object_per_line():
    record = logging.LogRecord("instamed.test", logging.WARNING, __file__, 1, "hi %s", ("x",), None)
    record.request_id = "req-1"

    line = json.loads(JsonFormatter().format(record))

    assert line["level"] == "WARNING"
    assert line["logger"] == "instamed.test"
    assert line["message"] == "hi x"
    assert line["request_id"] == "req-1"
    assert "ts" in line


def test_json_formatter_includes_exception():
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = logging.LogRecord("x", logging.ERROR, __file__, 1, "failed", (), sys.exc_info())
    record.request_id = "-"

    assert "ValueError: boom" in json.loads(JsonFormatter().format(record))["exception"]


def metric(text: str, name: str, **labels) -> float:
    for line in text.splitlines():
        if not (line.startswith(name + "{") or line.startswith(name + " ")):
            continue
        if all(f'{k}="{v}"' in line for k, v in labels.items()):
            return float(line.rsplit(" ", 1)[1])
    return 0.0


def test_metrics_count_requests_by_route_template(client):
    labels = {"route": "/medicines/{medicine_id}", "status": "404"}
    before = metric(client.get("/metrics").text, "http_requests_total", **labels)

    client.get("/medicines/000000000000000000000000", headers=NO_AUTH)
    text = client.get("/metrics").text

    assert metric(text, "http_requests_total", **labels) == before + 1
    # Raw ids never become labels.
    assert "000000000000000000000000" not in text
    assert "http_request_duration_seconds_bucket" in text


def test_metrics_count_orders_and_login_failures(client, shop, customer):  # noqa: F811
    text = client.get("/metrics").text
    orders_before = metric(text, "instamed_orders_placed_total")
    failures_before = metric(text, "instamed_login_failures_total")

    client.post(
        "/orders",
        json={"pincode": PINCODE, "items": [{"medicine_id": shop["otc"]["id"], "quantity": 1}]},
        headers=customer["headers"],
    )
    client.post(
        "/auth/login", data={"username": customer["email"], "password": "nope"}, headers=NO_AUTH
    )
    text = client.get("/metrics").text

    assert metric(text, "instamed_orders_placed_total") == orders_before + 1
    assert metric(text, "instamed_login_failures_total") == failures_before + 1


def test_metrics_token_protects_endpoint():
    settings = Settings(_env_file=None, metrics_token="scrape-secret-123")
    client = TestClient(create_app(settings))

    assert client.get("/metrics").status_code == 401
    ok = client.get("/metrics", headers={"Authorization": "Bearer scrape-secret-123"})
    assert ok.status_code == 200


def test_metrics_can_be_disabled():
    client = TestClient(create_app(Settings(_env_file=None, metrics_enabled=False)))

    assert client.get("/metrics").status_code == 404
