"""Production safety: config checks, docs toggle, CORS and security headers."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import DEV_JWT_SECRET, Settings
from app.main import create_app

STRONG_SECRET = "x" * 40


def prod_settings(**overrides) -> Settings:
    return Settings(
        _env_file=None,
        environment="production",
        jwt_secret=STRONG_SECRET,
        **overrides,
    )


@pytest.mark.parametrize("secret", [DEV_JWT_SECRET, "too-short-secret"])
def test_production_refuses_weak_jwt_secret(secret):
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(_env_file=None, environment="production", jwt_secret=secret)


def test_development_allows_dev_secret():
    settings = Settings(_env_file=None, environment="development", jwt_secret=DEV_JWT_SECRET)

    assert settings.uses_dev_jwt_secret


def test_docs_are_off_in_production_by_default():
    client = TestClient(create_app(prod_settings()))

    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_docs_can_be_enabled_in_production():
    client = TestClient(create_app(prod_settings(docs_enabled=True)))

    assert client.get("/docs").status_code == 200


def test_docs_are_on_in_development():
    client = TestClient(create_app(Settings(_env_file=None)))

    assert client.get("/openapi.json").status_code == 200


def preflight(client, origin):
    return client.options(
        "/medicines",
        headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
    )


def test_cors_allows_only_configured_origins():
    client = TestClient(create_app(prod_settings(cors_origins="https://app.instamed.example")))

    allowed = preflight(client, "https://app.instamed.example")
    blocked = preflight(client, "https://evil.example")

    assert allowed.headers["access-control-allow-origin"] == "https://app.instamed.example"
    assert "access-control-allow-origin" not in blocked.headers


def test_no_cors_headers_when_no_origins_configured():
    client = TestClient(create_app(Settings(_env_file=None)))

    assert "access-control-allow-origin" not in preflight(client, "https://x.example").headers


def test_security_headers_on_api_responses():
    response = TestClient(create_app(prod_settings())).get("/")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert (
        response.headers["Content-Security-Policy"] == "default-src 'none'; frame-ancestors 'none'"
    )
    assert response.headers["Strict-Transport-Security"].startswith("max-age=")


def test_no_hsts_outside_production_and_docs_keep_working_csp():
    client = TestClient(create_app(Settings(_env_file=None)))

    assert "Strict-Transport-Security" not in client.get("/").headers
    # Swagger UI loads scripts from a CDN, so the strict API CSP is not applied there.
    assert "Content-Security-Policy" not in client.get("/docs").headers


def test_secrets_never_appear_in_errors_or_repr():
    with pytest.raises(ValidationError) as exc:
        Settings(_env_file=None, environment="production", jwt_secret="leaky-but-short")

    assert "leaky-but-short" not in str(exc.value)
    settings = Settings(_env_file=None, jwt_secret=STRONG_SECRET, metrics_token="scrape-me-123")
    assert STRONG_SECRET not in repr(settings)
    assert "scrape-me-123" not in repr(settings)
