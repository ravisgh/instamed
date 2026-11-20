"""Shared test setup.

Tests talk to a real **local** MongoDB, in a throwaway database called `instamed_test`.
The guard below aborts the run if settings ever point anywhere else, so tests can
never touch Atlas or any other local database.
"""

import os
import tempfile
import urllib.request
from urllib.parse import urlparse

TEST_MONGO_URI = "mongodb://localhost:27017"
TEST_DB_NAME = "instamed_test"

# Must be set before the app (and its cached settings) is imported.
os.environ["MONGO_URI"] = TEST_MONGO_URI
os.environ["DB_NAME"] = TEST_DB_NAME
os.environ["JWT_SECRET"] = "test-secret-not-for-production-0123456789"
os.environ["BCRYPT_ROUNDS"] = "4"  # minimum cost: fast tests
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="instamed-test-uploads-")

# Elasticsearch tests run only when a local node answers; they use their own index.
TEST_ES_URL = "http://127.0.0.1:9200"
TEST_ES_INDEX = "instamed_test_medicines"


def _es_available() -> bool:
    try:
        with urllib.request.urlopen(TEST_ES_URL, timeout=1) as response:
            return response.status == 200
    except OSError:
        return False


ES_AVAILABLE = _es_available()
if ES_AVAILABLE:
    os.environ["ELASTICSEARCH_URL"] = TEST_ES_URL
    os.environ["ELASTICSEARCH_INDEX"] = TEST_ES_INDEX
    os.environ["ELASTICSEARCH_REFRESH"] = "true"
else:
    os.environ.pop("ELASTICSEARCH_URL", None)

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
    app.state.rate_limiter.reset()
    with TestClient(app) as test_client:
        test_client.headers.update(create_user("admin")["headers"])
        yield test_client
    with MongoClient(TEST_MONGO_URI, serverSelectionTimeoutMS=2000) as mongo:
        mongo.drop_database(TEST_DB_NAME)
    if ES_AVAILABLE:
        _drop_es_test_index()


def _drop_es_test_index() -> None:
    request = urllib.request.Request(f"{TEST_ES_URL}/{TEST_ES_INDEX}", method="DELETE")
    try:
        urllib.request.urlopen(request, timeout=5).close()
    except OSError:
        pass  # 404 when the index was never created


requires_es = pytest.mark.skipif(not ES_AVAILABLE, reason="no Elasticsearch on 127.0.0.1:9200")


@pytest.fixture
def pharmacist(client):
    return create_user("pharmacist")


@pytest.fixture
def customer(client):
    return create_user("customer")
