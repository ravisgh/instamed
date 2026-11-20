"""Shared test setup.

Tests talk to a real **local** MongoDB, in a throwaway database called `instamed_test`.
The guard below aborts the run if settings ever point anywhere else, so tests can
never touch Atlas or any other local database.
"""

import os
from urllib.parse import urlparse

TEST_MONGO_URI = "mongodb://localhost:27017"
TEST_DB_NAME = "instamed_test"

# Must be set before the app (and its cached settings) is imported.
os.environ["MONGO_URI"] = TEST_MONGO_URI
os.environ["DB_NAME"] = TEST_DB_NAME

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from pymongo import MongoClient  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402

ALLOWED_HOSTS = {"localhost", "127.0.0.1"}


def _assert_safe_target() -> None:
    settings = get_settings()
    host = urlparse(settings.mongo_uri).hostname
    if settings.db_name != TEST_DB_NAME or host not in ALLOWED_HOSTS:
        pytest.exit(
            f"Refusing to run tests against db={settings.db_name!r} host={host!r}",
            returncode=2,
        )


_assert_safe_target()


@pytest.fixture
def client():
    """A TestClient with the app's lifespan running; wipes instamed_test afterwards."""
    with TestClient(app) as test_client:
        yield test_client
    with MongoClient(TEST_MONGO_URI, serverSelectionTimeoutMS=2000) as mongo:
        mongo.drop_database(TEST_DB_NAME)
