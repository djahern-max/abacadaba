import uuid

from sqlalchemy import and_

# Shared by app/services/watch.py (feature 015) and app/services/review.py
# (feature 023) - both watch_progress and review_responses key a row to a
# viewer_id/user_id pair the same way, and both need the same non-OR
# resolution rule to avoid leaking one signed-in user's rows to another
# person sharing a browser: a signed-in user's row is found by user_id
# alone; an anonymous viewer's row by viewer_id alone, and only among rows
# nobody has claimed. The two halves never both apply to the same row.


def identity_filter(user_id_column, viewer_id_column, viewer_id: uuid.UUID, user_id: int | None):
    if user_id is not None:
        return user_id_column == user_id
    return and_(viewer_id_column == viewer_id, user_id_column.is_(None))
