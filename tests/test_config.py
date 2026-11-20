from app.core.config import Settings


def test_settings_defaults(monkeypatch):
    monkeypatch.delenv("MONGO_URI", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)

    # _env_file=None ignores any local .env so the test only sees defaults
    settings = Settings(_env_file=None)

    assert settings.app_name == "InstaMed API"
    assert settings.mongo_uri == "mongodb://localhost:27017"
    assert settings.db_name == "instamed"


def test_settings_read_from_environment(monkeypatch):
    monkeypatch.setenv("MONGO_URI", "mongodb://db.example:27017")
    monkeypatch.setenv("DB_NAME", "instamed_test")

    settings = Settings(_env_file=None)

    assert settings.mongo_uri == "mongodb://db.example:27017"
    assert settings.db_name == "instamed_test"
