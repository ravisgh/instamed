import logging

from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app


class _BrokenDb:
    """Stands in for the database when we want every call to fail."""

    def __getitem__(self, name):
        raise RuntimeError("database exploded")

    async def command(self, *args, **kwargs):
        raise RuntimeError("database unreachable")


def test_health_reports_ok_when_db_answers(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_reports_503_when_db_is_down(client):
    app.dependency_overrides[get_db] = lambda: _BrokenDb()
    try:
        response = client.get("/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unreachable"}


def test_request_id_is_generated_and_returned(client):
    response = client.get("/")

    assert len(response.headers["X-Request-ID"]) >= 16


def test_incoming_request_id_is_kept(client):
    response = client.get("/", headers={"X-Request-ID": "abc-123"})

    assert response.headers["X-Request-ID"] == "abc-123"


def test_unhandled_error_returns_json_500_with_request_id(client):
    app.dependency_overrides[get_db] = lambda: _BrokenDb()
    try:
        with TestClient(app, raise_server_exceptions=False) as raw:
            response = raw.get("/medicines", headers={"X-Request-ID": "req-500"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error", "request_id": "req-500"}
    assert "database exploded" not in response.text


def test_each_request_is_logged(client, caplog):
    with caplog.at_level(logging.INFO, logger="instamed.access"):
        client.get("/", headers={"X-Request-ID": "log-1"})

    record = next(r for r in caplog.records if r.name == "instamed.access")
    assert "GET / 200" in record.getMessage()
    assert record.request_id == "log-1"
