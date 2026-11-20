from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, read from environment variables or a local .env file.

    Field names map to env vars case-insensitively: mongo_uri <- MONGO_URI.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "InstaMed API"
    mongo_uri: str = "mongodb://localhost:27017"
    db_name: str = "instamed"


@lru_cache
def get_settings() -> Settings:
    """Build Settings once and reuse it everywhere."""
    return Settings()
