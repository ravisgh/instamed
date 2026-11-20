import pytest

from scripts.create_admin import PASSWORD_ENV, main
from tests.conftest import NO_AUTH, TEST_DB_NAME


def login(client, email, password):
    return client.post(
        "/auth/login", data={"username": email, "password": password}, headers=NO_AUTH
    )


def test_creates_admin_who_can_log_in(client, monkeypatch, capsys):
    monkeypatch.setenv(PASSWORD_ENV, "boss-password-1")

    main(["--email", "Boss@Example.com", "--db", TEST_DB_NAME])

    assert "Created admin boss@example.com" in capsys.readouterr().out
    token = login(client, "boss@example.com", "boss-password-1").json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    assert me["role"] == "admin"


def test_promotes_existing_customer(client, customer, monkeypatch, capsys):
    monkeypatch.setenv(PASSWORD_ENV, "new-password-12")

    main(["--email", customer["email"], "--db", TEST_DB_NAME])

    assert "Promoted/updated" in capsys.readouterr().out
    assert client.get("/auth/me", headers=customer["headers"]).json()["role"] == "admin"


def test_refuses_non_dev_database(monkeypatch):
    monkeypatch.setenv(PASSWORD_ENV, "whatever-123")

    with pytest.raises(SystemExit):
        main(["--email", "a@example.com", "--db", "rio_debugger"])


def test_rejects_short_password(client, monkeypatch):
    monkeypatch.setenv(PASSWORD_ENV, "short")

    with pytest.raises(SystemExit):
        main(["--email", "a@example.com", "--db", TEST_DB_NAME])
