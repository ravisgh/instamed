"""Shared test setup.

Tests talk to a real **local** MongoDB, in a throwaway database called `instamed_test`.
The guard below aborts the run if settings ever point anywhere else, so tests can
never touch Atlas or any other local database.
"""

import os
import tempfile
from urllib.parse import urlparse

TEST_MONGO_URI = "mongodb://localhost:27017"
TEST_DB_NAME = "instamed_test"

# Must be set before the app (and its cached settings) is imported.
os.environ["MONGO_URI"] = TEST_MONGO_URI
os.environ["DB_NAME"] = TEST_DB_NAME
os.environ["JWT_SECRET"] = "test-secret-not-for-production-0123456789"
os.environ["BCRYPT_ROUNDS"] = "4"  # minimum cost: fast tests
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="instamed-test-uploads-")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from pymongo import MongoClient  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.main import app  # noqa: E402

ALLOWED_HOSTS = {"localhost", "127.0.0.1"}
TEST_PASSWORD = "correct-horse-battery"
NO_AUTH = {"Authorization": ""}  # per-request override that drops the default admin token


def _assert_safe_target() -> None:
    settings = get_settings()
    host = urlparse(settings.mongo_uri).hostname
    if settings.db_name != TEST_DB_NAME or host not in ALLOWED_HOSTS:
        pytest.exit(
            f"Refusing to run tests against db={settings.db_name!r} host={host!r}",
            returncode=2,
        )


_assert_safe_target()


def create_user(role: str, email: str | None = None) -> dict:
    """Insert a user straight into instamed_test and return it with a ready token."""
    email = email or f"{role}@instamed.example"
    with MongoClient(TEST_MONGO_URI) as mongo:
        result = mongo[TEST_DB_NAME]["users"].insert_one(
            {
                "email": email,
                "full_name": f"Test {role.title()}",
                "role": role,
                "is_active": True,
                "password_hash": hash_password(TEST_PASSWORD),
            }
        )
    user_id = str(result.inserted_id)
    token = create_access_token(user_id, role)
    return {"id": user_id, "email": email, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def client():
    """TestClient with the app's lifespan running, logged in as an admin by default.

    Pass `headers=NO_AUTH` (or another user's headers) on a request to act as someone else.
    Wipes instamed_test afterwards.
    """
    with TestClient(app) as test_client:
        test_client.headers.update(create_user("admin")["headers"])
        yield test_client
    with MongoClient(TEST_MONGO_URI, serverSelectionTimeoutMS=2000) as mongo:
        mongo.drop_database(TEST_DB_NAME)


@pytest.fixture
def pharmacist(client):
    return create_user("pharmacist")


@pytest.fixture
def customer(client):
    return create_user("customer")
