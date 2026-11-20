"""Refresh-token rotation, reuse detection, logout and password change."""

from datetime import UTC, datetime, timedelta

from pymongo import MongoClient

from tests.conftest import NO_AUTH, TEST_DB_NAME, TEST_MONGO_URI, TEST_PASSWORD


def login(client, email, password=TEST_PASSWORD):
    response = client.post(
        "/auth/login", data={"username": email, "password": password}, headers=NO_AUTH
    )
    return response


def refresh(client, token):
    return client.post("/auth/refresh", json={"refresh_token": token}, headers=NO_AUTH)


def bearer(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_login_returns_access_and_refresh_tokens(client, customer):
    body = login(client, customer["email"]).json()

    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 15 * 60
    assert len(body["refresh_token"]) >= 40
    assert client.get("/auth/me", headers=bearer(body)).status_code == 200


def test_refresh_rotates_tokens(client, customer):
    first = login(client, customer["email"]).json()

    second = refresh(client, first["refresh_token"])

    assert second.status_code == 200
    assert second.json()["refresh_token"] != first["refresh_token"]
    assert client.get("/auth/me", headers=bearer(second.json())).status_code == 200


def test_reusing_a_refresh_token_revokes_the_whole_family(client, customer):
    first = login(client, customer["email"]).json()
    second = refresh(client, first["refresh_token"]).json()

    stolen = refresh(client, first["refresh_token"])  # old token used again

    assert stolen.status_code == 401
    assert refresh(client, second["refresh_token"]).status_code == 401  # family revoked


def test_refresh_tokens_are_stored_hashed(client, customer):
    token = login(client, customer["email"]).json()["refresh_token"]

    with MongoClient(TEST_MONGO_URI) as mongo:
        stored = mongo[TEST_DB_NAME]["refresh_tokens"].find_one({})

    assert token not in str(stored)


def test_expired_or_unknown_refresh_token_is_401(client, customer):
    token = login(client, customer["email"]).json()["refresh_token"]
    with MongoClient(TEST_MONGO_URI) as mongo:
        mongo[TEST_DB_NAME]["refresh_tokens"].update_many(
            {}, {"$set": {"expires_at": datetime.now(UTC) - timedelta(seconds=1)}}
        )

    assert refresh(client, token).status_code == 401
    assert refresh(client, "made-up-token-" * 4).status_code == 401


def test_deactivated_user_cannot_refresh(client, customer):
    token = login(client, customer["email"]).json()["refresh_token"]
    client.patch(f"/users/{customer['id']}", json={"is_active": False})

    assert refresh(client, token).status_code == 401


def test_logout_revokes_refresh_token(client, customer):
    token = login(client, customer["email"]).json()["refresh_token"]

    response = client.post("/auth/logout", json={"refresh_token": token}, headers=NO_AUTH)

    assert response.status_code == 204
    assert refresh(client, token).status_code == 401


def test_change_password_invalidates_old_tokens(client, customer):
    old = login(client, customer["email"]).json()

    changed = client.post(
        "/auth/change-password",
        json={"current_password": TEST_PASSWORD, "new_password": "brand-new-password-9"},
        headers=bearer(old),
    )

    assert changed.status_code == 204
    assert client.get("/auth/me", headers=bearer(old)).status_code == 401
    assert refresh(client, old["refresh_token"]).status_code == 401
    assert login(client, customer["email"]).status_code == 401
    assert login(client, customer["email"], "brand-new-password-9").status_code == 200


def test_change_password_checks_current_password(client, customer):
    tokens = login(client, customer["email"]).json()

    wrong = client.post(
        "/auth/change-password",
        json={"current_password": "not-my-password", "new_password": "brand-new-password-9"},
        headers=bearer(tokens),
    )
    short = client.post(
        "/auth/change-password",
        json={"current_password": TEST_PASSWORD, "new_password": "short"},
        headers=bearer(tokens),
    )

    assert wrong.status_code == 400
    assert short.status_code == 422
