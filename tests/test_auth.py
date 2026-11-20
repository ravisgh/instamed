from datetime import timedelta

import pytest

from app.core.security import create_access_token, hash_password, verify_password
from tests.conftest import NO_AUTH, TEST_PASSWORD

NEW_USER = {
    "email": "Asha.Verma@Example.com",
    "password": "s3cure-passw0rd",
    "full_name": "Asha Verma",
}


def register(client, **overrides):
    return client.post("/auth/register", json={**NEW_USER, **overrides}, headers=NO_AUTH)


def login(client, email, password):
    return client.post(
        "/auth/login", data={"username": email, "password": password}, headers=NO_AUTH
    )


def test_password_hashing_round_trip():
    hashed = hash_password("hunter2-hunter2")

    assert hashed != "hunter2-hunter2"
    assert verify_password("hunter2-hunter2", hashed)
    assert not verify_password("wrong", hashed)


def test_register_creates_customer_without_leaking_hash(client):
    response = register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "asha.verma@example.com"  # normalised
    assert body["role"] == "customer"
    assert body["is_active"] is True
    assert "password" not in body and "password_hash" not in body


def test_register_ignores_role_in_body(client):
    response = register(client, role="admin")

    assert response.json()["role"] == "customer"


def test_register_duplicate_email_any_case_is_409(client):
    register(client)

    assert register(client, email="ASHA.VERMA@example.com").status_code == 409


@pytest.mark.parametrize(
    "overrides",
    [{"email": "not-an-email"}, {"password": "short"}, {"password": "x" * 73}, {"full_name": ""}],
)
def test_register_validation(client, overrides):
    assert register(client, **overrides).status_code == 422


def test_login_returns_bearer_token_and_me_works(client):
    register(client)

    response = login(client, "asha.verma@example.com", NEW_USER["password"])

    assert response.status_code == 200
    token = response.json()
    assert token["token_type"] == "bearer"
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "asha.verma@example.com"


@pytest.mark.parametrize(
    ("email", "password"),
    [("asha.verma@example.com", "wrong-password"), ("nobody@example.com", "whatever-123")],
)
def test_login_failures_are_401_with_same_message(client, email, password):
    register(client)

    response = login(client, email, password)

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_me_requires_valid_token(client):
    assert client.get("/auth/me", headers=NO_AUTH).status_code == 401
    bad = client.get("/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert bad.status_code == 401
    assert bad.headers["WWW-Authenticate"] == "Bearer"


def test_expired_token_is_rejected(client, customer):
    token = create_access_token(customer["id"], "customer", expires_in=timedelta(seconds=-1))

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_deactivated_user_is_rejected(client, customer):
    client.patch(f"/users/{customer['id']}", json={"is_active": False})

    assert client.get("/auth/me", headers=customer["headers"]).status_code == 401
    assert login(client, customer["email"], TEST_PASSWORD).status_code == 401


def test_admin_manages_staff(client):
    created = client.post(
        "/users",
        json={**NEW_USER, "email": "pharma@example.com", "role": "pharmacist"},
    )

    assert created.status_code == 201
    assert created.json()["role"] == "pharmacist"
    assert len(client.get("/users").json()) == 2  # fixture admin + new pharmacist
    promoted = client.patch(f"/users/{created.json()['id']}", json={"role": "admin"})
    assert promoted.json()["role"] == "admin"


def test_non_admins_cannot_manage_users(client, pharmacist, customer):
    for user in (pharmacist, customer):
        assert client.get("/users", headers=user["headers"]).status_code == 403
        assert (
            client.post(
                "/users", json={**NEW_USER, "role": "admin"}, headers=user["headers"]
            ).status_code
            == 403
        )
