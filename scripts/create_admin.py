"""Create (or promote) an admin user in a LOCAL dev database.

Usage (PowerShell, from the repo root):
    python -m scripts.create_admin --email you@example.com --full-name "Your Name"

The password is asked for twice at the prompt (not echoed). For automation, set the
INSTAMED_ADMIN_PASSWORD environment variable instead. Same local-only guard as the
seed script: localhost + instamed_dev / instamed_test only.
"""

import argparse
import getpass
import os
import sys
from collections.abc import Sequence

from pydantic import ValidationError
from pymongo import MongoClient

from app.core.security import hash_password
from app.models.user import UserRegister
from scripts.safety import check_target

PASSWORD_ENV = "INSTAMED_ADMIN_PASSWORD"


def _read_password() -> str:
    from_env = os.environ.get(PASSWORD_ENV)
    if from_env:
        return from_env
    first = getpass.getpass("Admin password: ")
    if first != getpass.getpass("Repeat password: "):
        sys.exit("Passwords do not match.")
    return first


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--email", required=True)
    parser.add_argument("--full-name", default="InstaMed Admin")
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017")
    parser.add_argument("--db", default="instamed_dev")
    args = parser.parse_args(argv)

    check_target(args.mongo_uri, args.db)
    try:
        body = UserRegister(email=args.email, password=_read_password(), full_name=args.full_name)
    except ValidationError as exc:
        sys.exit(f"Invalid input: {exc.errors()[0]['loc'][0]}: {exc.errors()[0]['msg']}")

    with MongoClient(args.mongo_uri, serverSelectionTimeoutMS=3000) as mongo:
        users = mongo[args.db]["users"]
        users.create_index("email", unique=True)
        result = users.update_one(
            {"email": body.email},
            {
                "$set": {
                    "full_name": body.full_name,
                    "role": "admin",
                    "is_active": True,
                    "password_hash": hash_password(body.password),
                }
            },
            upsert=True,
        )
    action = "Created" if result.upserted_id else "Promoted/updated"
    print(f"{action} admin {body.email} in {args.db}")


if __name__ == "__main__":
    main()
