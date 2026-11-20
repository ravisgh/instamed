from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_returns_running_message():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "InstaMed backend is running!"}


def test_openapi_uses_app_title():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "InstaMed API"
