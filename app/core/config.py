from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Only for local development; the app logs a warning at startup while it is in use.
DEV_JWT_SECRET = "dev-only-insecure-jwt-secret-change-me"
MIN_PROD_SECRET_LENGTH = 32


class Settings(BaseSettings):
    """App configuration, read from environment variables or a local .env file.

    Field names map to env vars case-insensitively: mongo_uri <- MONGO_URI.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "InstaMed API"
    environment: Literal["development", "test", "production"] = "development"
    # Interactive /docs and /openapi.json. Default: on, except in production.
    docs_enabled: bool | None = None
    # Comma-separated browser origins allowed to call the API (CORS). Empty = none.
    cors_origins: str = ""
    mongo_uri: str = "mongodb://localhost:27017"
    db_name: str = "instamed"
    log_level: str = "INFO"
    log_format: Literal["text", "json"] = "text"

    # Prometheus metrics at /metrics. Set METRICS_TOKEN to require a bearer token.
    metrics_enabled: bool = True
    metrics_token: str | None = None

    # Auth. Override JWT_SECRET in every real deployment (32+ random characters).
    jwt_secret: str = DEV_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 14
    bcrypt_rounds: int = 12  # cost factor; tests lower it for speed

    # Brute-force protection (per process; see app/core/rate_limit.py).
    rate_limit_enabled: bool = True
    login_attempts_per_email_per_minute: int = 5
    login_attempts_per_ip_per_minute: int = 20
    registrations_per_ip_per_hour: int = 10

    # Prescription uploads are stored on local disk (kept out of git).
    upload_dir: str = "uploads"
    max_upload_bytes: int = 5 * 1024 * 1024

    # Optional Elasticsearch for /medicines/search. Unset = Mongo fallback only.
    elasticsearch_url: str | None = None
    elasticsearch_index: str = "medicines"
    elasticsearch_refresh: bool = False  # true = writes searchable immediately (tests)

    @property
    def uses_dev_jwt_secret(self) -> bool:
        return self.jwt_secret == DEV_JWT_SECRET

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def show_docs(self) -> bool:
        return self.docs_enabled if self.docs_enabled is not None else not self.is_production

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def _production_must_be_safe(self):
        if self.is_production and (
            self.uses_dev_jwt_secret or len(self.jwt_secret) < MIN_PROD_SECRET_LENGTH
        ):
            raise ValueError(
                f"JWT_SECRET must be set to a random value of at least "
                f"{MIN_PROD_SECRET_LENGTH} characters when ENVIRONMENT=production"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Build Settings once and reuse it everywhere."""
    return Settings()
