from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Only for local development; the app logs a warning at startup while it is in use.
DEV_JWT_SECRET = "dev-only-insecure-jwt-secret-change-me"


class Settings(BaseSettings):
    """App configuration, read from environment variables or a local .env file.

    Field names map to env vars case-insensitively: mongo_uri <- MONGO_URI.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "InstaMed API"
    mongo_uri: str = "mongodb://localhost:27017"
    db_name: str = "instamed"
    log_level: str = "INFO"

    # Auth. Override JWT_SECRET in every real deployment (32+ random characters).
    jwt_secret: str = DEV_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    bcrypt_rounds: int = 12  # cost factor; tests lower it for speed

    @property
    def uses_dev_jwt_secret(self) -> bool:
        return self.jwt_secret == DEV_JWT_SECRET


@lru_cache
def get_settings() -> Settings:
    """Build Settings once and reuse it everywhere."""
    return Settings()
