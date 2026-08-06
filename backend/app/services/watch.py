import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.lesson import Lesson
from app.models.watch_progress import WatchProgress

# A real heartbeat cadence is ~10s, comfortably clearing both thresholds below.
MIN_POST_INTERVAL_SECONDS = 5
MIN_CREDIT_INTERVAL_SECONDS = 8
MAX_POSITION_JUMP_SECONDS = 15


class RateLimitedError(Exception):
    """Raised when a heartbeat arrives faster than the minimum POST spacing."""


@dataclass
class WatchProgressData:
    watched_seconds: int
    required_seconds: int | None
    ratio: float
    unlocked: bool


def _required_seconds(lesson: Lesson) -> int | None:
    if lesson.duration_seconds is None:
        return None
    return round(lesson.duration_seconds * lesson.required_watch_ratio)


def _progress_data(watched_seconds: int, lesson: Lesson) -> WatchProgressData:
    required = _required_seconds(lesson)
    if not required:
        # Nothing to measure against, so the lesson is ungated.
        return WatchProgressData(
            watched_seconds=watched_seconds, required_seconds=required, ratio=1.0, unlocked=True
        )
    ratio = min(watched_seconds / required, 1.0)
    return WatchProgressData(
        watched_seconds=watched_seconds,
        required_seconds=required,
        ratio=ratio,
        unlocked=watched_seconds >= required,
    )


def _identity_filter(viewer_id: uuid.UUID, user_id: int | None):
    if user_id is not None:
        return or_(WatchProgress.viewer_id == viewer_id, WatchProgress.user_id == user_id)
    return WatchProgress.viewer_id == viewer_id


def _best_watched_seconds(db: Session, lesson_id: int, viewer_id: uuid.UUID, user_id: int | None) -> int:
    # A signed in user's progress follows them across devices/cookies, so the
    # best (most-watched) row across every viewer_id tied to this identity wins.
    stmt = select(func.max(WatchProgress.watched_seconds)).where(
        WatchProgress.lesson_id == lesson_id, _identity_filter(viewer_id, user_id)
    )
    return db.execute(stmt).scalar() or 0


def _get_or_create_locked(db: Session, lesson_id: int, viewer_id: uuid.UUID) -> WatchProgress:
    stmt = (
        select(WatchProgress)
        .where(WatchProgress.lesson_id == lesson_id, WatchProgress.viewer_id == viewer_id)
        .with_for_update()
    )
    progress = db.execute(stmt).scalar_one_or_none()
    if progress is not None:
        return progress

    progress = WatchProgress(lesson_id=lesson_id, viewer_id=viewer_id)
    db.add(progress)
    try:
        db.flush()
    except IntegrityError:
        # Lost a race with a concurrent first heartbeat for the same viewer;
        # the other transaction's row now exists, so re-fetch it locked.
        db.rollback()
        progress = db.execute(stmt).scalar_one()
    return progress


def record_heartbeat(
    db: Session, lesson: Lesson, viewer_id: uuid.UUID, user_id: int | None, position: int
) -> WatchProgressData:
    progress = _get_or_create_locked(db, lesson.id, viewer_id)
    now = datetime.now(timezone.utc)

    if progress.last_heartbeat_at is not None:
        wall_delta = (now - progress.last_heartbeat_at).total_seconds()
        if wall_delta < MIN_POST_INTERVAL_SECONDS:
            db.rollback()
            raise RateLimitedError("Heartbeats are limited to about one every five seconds")

        position_delta = position - progress.last_position
        within_duration = lesson.duration_seconds is None or position <= lesson.duration_seconds
        if (
            0 <= position_delta <= MAX_POSITION_JUMP_SECONDS
            and wall_delta >= MIN_CREDIT_INTERVAL_SECONDS
            and within_duration
        ):
            progress.watched_seconds += int(min(position_delta, wall_delta))
        # A backward or too-large jump earns no credit, but the position and
        # timestamp below still advance, so the next heartbeat compares
        # against where the viewer actually is now.

    progress.last_position = position
    progress.last_heartbeat_at = now
    if user_id is not None:
        progress.user_id = user_id

    required = _required_seconds(lesson)
    if progress.completed_at is None and required and progress.watched_seconds >= required:
        progress.completed_at = now

    db.commit()

    watched_seconds = _best_watched_seconds(db, lesson.id, viewer_id, user_id)
    return _progress_data(watched_seconds, lesson)


def get_progress(db: Session, lesson: Lesson, viewer_id: uuid.UUID, user_id: int | None = None) -> WatchProgressData:
    watched_seconds = _best_watched_seconds(db, lesson.id, viewer_id, user_id)
    return _progress_data(watched_seconds, lesson)


def is_unlocked(db: Session, lesson: Lesson, viewer_id: uuid.UUID, user_id: int | None = None) -> bool:
    return get_progress(db, lesson, viewer_id, user_id).unlocked
