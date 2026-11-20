"""Shared guard for scripts that write to MongoDB: local dev/test databases only."""

import sys
from urllib.parse import urlparse

ALLOWED_HOSTS = {"localhost", "127.0.0.1"}
ALLOWED_DBS = {"instamed_dev", "instamed_test"}


def check_target(mongo_uri: str, db_name: str) -> None:
    """Exit unless we are pointed at a local dev/test database."""
    host = urlparse(mongo_uri).hostname
    if host not in ALLOWED_HOSTS or db_name not in ALLOWED_DBS:
        sys.exit(
            f"Refusing to write to host={host!r} db={db_name!r}. "
            f"Allowed hosts: {sorted(ALLOWED_HOSTS)}, dbs: {sorted(ALLOWED_DBS)}."
        )
