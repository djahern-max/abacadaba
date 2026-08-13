"""Wipe all application data: every table, plus every object in the Spaces bucket.

Development tooling, not a feature. This exists so a manual test run can start
from genuinely nothing rather than from whatever the last run left behind.

The database and the bucket are cleared together on purpose. Clearing only the
bucket leaves rows whose video_key points at a deleted object, which surfaces as
AccessDenied on an otherwise valid presigned URL and reads like a credentials
bug. Clearing only the database leaves orphaned objects nothing references.

The database is truncated first. If the Spaces purge then fails partway, the
leftovers are orphans and a re-run cleans them up; the reverse order would leave
dangling references instead.

Note that local and production currently share the abacadaba bucket, so running
this from a laptop also clears production's objects. That is accepted while
everything in it is test data. A separate dev bucket is the fix when it isn't.

    python -m scripts.reset_data
    python -m scripts.reset_data --yes
"""

import argparse
import sys

from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.config import settings
from app.db import SessionLocal
from app.services import storage

# Child tables first. TRUNCATE ... CASCADE makes the order irrelevant to
# Postgres, but reading it dependency-first makes the shape of the schema
# obvious to whoever runs this next.
TABLES = [
    "attempt_answers",
    "attempts",
    "watch_progress",
    "choices",
    "questions",
    "learning_objectives",
    "lessons",
    "courses",
    "sessions",
    "users",
]


def database_target() -> str:
    """The database host and name, with the password redacted."""
    return make_url(settings.database_url).render_as_string(hide_password=True)


def row_counts(db) -> dict[str, int]:
    return {
        table: db.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
        for table in TABLES
    }


def object_keys() -> list[str]:
    """Every key in the bucket.

    Paginated because a bare list_objects_v2 truncates at 1000 keys without
    saying so.
    """
    paginator = storage._client.get_paginator("list_objects_v2")
    return [
        obj["Key"]
        for page in paginator.paginate(Bucket=settings.spaces_bucket)
        for obj in page.get("Contents", [])
    ]


def truncate_all(db) -> None:
    db.execute(
        text(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE")
    )
    db.commit()


def delete_objects(keys: list[str]) -> int:
    """Delete every key, in batches of 1000 (the S3 API's hard limit)."""
    deleted = 0
    for start in range(0, len(keys), 1000):
        batch = [{"Key": key} for key in keys[start : start + 1000]]
        response = storage._client.delete_objects(
            Bucket=settings.spaces_bucket,
            Delete={"Objects": batch},
        )
        deleted += len(response.get("Deleted", []))
        for error in response.get("Errors", []):
            print(f"  ERROR {error.get('Key')}: {error.get('Message')}")
    return deleted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--yes",
        action="store_true",
        help="skip the confirmation prompt",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        counts = row_counts(db)
        keys = object_keys()

        print(f"database: {database_target()}")
        print(f"bucket:   {settings.spaces_bucket}")
        print()
        for table, count in counts.items():
            print(f"  {count:>6,}  {table}")
        print(f"  {len(keys):>6,}  objects in Spaces")
        print()

        if not counts and not keys:
            print("Nothing to do.")
            return 0

        if not args.yes:
            print(f"This deletes all of it. Type the bucket name to confirm.")
            if input("> ").strip() != settings.spaces_bucket:
                print("Aborted.")
                return 1
            print()

        truncate_all(db)
        print(f"truncated {len(TABLES)} tables, sequences reset")

        if keys:
            deleted = delete_objects(keys)
            print(f"deleted {deleted} of {len(keys)} objects")

        remaining_rows = sum(row_counts(db).values())
        remaining_objects = len(object_keys())
        print()
        print(f"verify: {remaining_rows} rows, {remaining_objects} objects")
        return 0 if remaining_rows == 0 and remaining_objects == 0 else 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
