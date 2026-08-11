"""watch progress identity indexes

Revision ID: 6f58cd9b86ef
Revises: e3f7657ace02
Create Date: 2026-08-11 18:13:44.817755

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f58cd9b86ef'
down_revision: Union[str, None] = 'e3f7657ace02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_CONSTRAINT_NAME = "watch_progress_lesson_id_viewer_id_key"
USER_INDEX_NAME = "ix_watch_progress_lesson_user_unique"
VIEWER_INDEX_NAME = "ix_watch_progress_lesson_viewer_unique"

# The old constraint was (lesson_id, viewer_id) with no regard to user_id, so
# duplicate (lesson_id, viewer_id) rows are impossible today. But one user_id
# can be attached to rows from several viewer_ids (one per browser/device),
# so (lesson_id, user_id) can already have duplicates. Collapse those before
# the new unique index is created, keeping the lowest id per group as the
# survivor and folding the best values from its siblings into it.
_MERGE_DUPLICATES_SQL = """
    UPDATE watch_progress wp
    SET watched_seconds = agg.best_watched_seconds,
        last_position = agg.best_last_position,
        last_heartbeat_at = agg.best_last_heartbeat_at,
        completed_at = agg.best_completed_at
    FROM (
        SELECT
            MIN(id) AS keeper_id,
            MAX(watched_seconds) AS best_watched_seconds,
            MAX(last_position) AS best_last_position,
            MAX(last_heartbeat_at) AS best_last_heartbeat_at,
            MIN(completed_at) AS best_completed_at
        FROM watch_progress
        WHERE user_id IS NOT NULL
        GROUP BY lesson_id, user_id
        HAVING COUNT(*) > 1
    ) AS agg
    WHERE wp.id = agg.keeper_id
"""

_DELETE_DUPLICATES_SQL = """
    DELETE FROM watch_progress wp
    WHERE wp.user_id IS NOT NULL
      AND wp.id NOT IN (
          SELECT MIN(id)
          FROM watch_progress
          WHERE user_id IS NOT NULL
          GROUP BY lesson_id, user_id
      )
"""


def upgrade() -> None:
    op.execute(_MERGE_DUPLICATES_SQL)
    op.execute(_DELETE_DUPLICATES_SQL)

    op.drop_constraint(OLD_CONSTRAINT_NAME, "watch_progress", type_="unique")

    op.create_index(
        USER_INDEX_NAME,
        "watch_progress",
        ["lesson_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )
    op.create_index(
        VIEWER_INDEX_NAME,
        "watch_progress",
        ["lesson_id", "viewer_id"],
        unique=True,
        postgresql_where=sa.text("user_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(VIEWER_INDEX_NAME, table_name="watch_progress")
    op.drop_index(USER_INDEX_NAME, table_name="watch_progress")

    op.create_unique_constraint(OLD_CONSTRAINT_NAME, "watch_progress", ["lesson_id", "viewer_id"])
