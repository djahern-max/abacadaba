import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.lesson import Lesson
from app.models.user import User
from app.models.watch_progress import WatchProgress
from app.services.identity import identity_filter

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
    duration_seconds: int | None
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
            watched_seconds=watched_seconds,
            required_seconds=required,
            duration_seconds=lesson.duration_seconds,
            ratio=1.0,
            unlocked=True,
        )
    ratio = min(watched_seconds / required, 1.0)
    return WatchProgressData(
        watched_seconds=watched_seconds,
        required_seconds=required,
        duration_seconds=lesson.duration_seconds,
        ratio=ratio,
        unlocked=watched_seconds >= required,
    )


def _identity_filter(viewer_id: uuid.UUID, user_id: int | None):
    # See app/services/identity.py for the resolution rule this applies.
    # Matches the partial unique indexes in migration 6f58cd9b86ef.
    return identity_filter(WatchProgress.user_id, WatchProgress.viewer_id, viewer_id, user_id)


def _best_watched_seconds(db: Session, lesson_id: int, viewer_id: uuid.UUID, user_id: int | None) -> int:
    stmt = select(WatchProgress.watched_seconds).where(
        WatchProgress.lesson_id == lesson_id, _identity_filter(viewer_id, user_id)
    )
    return db.execute(stmt).scalar() or 0


def _get_or_create_locked(
    db: Session, lesson_id: int, viewer_id: uuid.UUID, user_id: int | None
) -> WatchProgress:
    identity_filter = _identity_filter(viewer_id, user_id)
    stmt = (
        select(WatchProgress).where(WatchProgress.lesson_id == lesson_id, identity_filter).with_for_update()
    )
    progress = db.execute(stmt).scalar_one_or_none()
    if progress is not None:
        return progress

    progress = WatchProgress(lesson_id=lesson_id, viewer_id=viewer_id, user_id=user_id)
    db.add(progress)
    try:
        db.flush()
    except IntegrityError:
        # Lost a race with a concurrent first heartbeat for the same identity;
        # the other transaction's row now exists, so re-fetch it locked.
        db.rollback()
        progress = db.execute(stmt).scalar_one()
    return progress


def claim_anonymous_progress(db: Session, viewer_id: uuid.UUID, user: User) -> None:
    """Fold this browser's anonymous progress into the signed-in user's rows.

    Runs once at sign in (register, login, Google callback), before the
    redirect. For each lesson where this viewer_id has unclaimed (NULL
    user_id) progress, either hand the row to the user outright, or, if the
    user already has their own row for that lesson, merge by taking the
    larger watched_seconds and drop the anonymous row. Merging rather than
    overwriting means a returning user never loses progress to a shorter
    anonymous session on the same browser. Safe to call repeatedly: once a
    row is claimed or merged away, a later call finds nothing left to do.
    """
    anonymous_rows = (
        db.execute(
            select(WatchProgress)
            .where(WatchProgress.viewer_id == viewer_id, WatchProgress.user_id.is_(None))
            .with_for_update()
        )
        .scalars()
        .all()
    )

    for anon in anonymous_rows:
        existing = db.execute(
            select(WatchProgress)
            .where(WatchProgress.lesson_id == anon.lesson_id, WatchProgress.user_id == user.id)
            .with_for_update()
        ).scalar_one_or_none()

        if existing is None:
            anon.user_id = user.id
            continue

        existing.watched_seconds = max(existing.watched_seconds, anon.watched_seconds)
        existing.last_position = max(existing.last_position, anon.last_position)
        if anon.last_heartbeat_at is not None and (
            existing.last_heartbeat_at is None or anon.last_heartbeat_at > existing.last_heartbeat_at
        ):
            existing.last_heartbeat_at = anon.last_heartbeat_at
        if anon.completed_at is not None and (
            existing.completed_at is None or anon.completed_at < existing.completed_at
        ):
            existing.completed_at = anon.completed_at
        db.delete(anon)

    db.commit()


def record_heartbeat(
    db: Session, lesson: Lesson, viewer_id: uuid.UUID, user_id: int | None, position: int
) -> WatchProgressData:
    progress = _get_or_create_locked(db, lesson.id, viewer_id, user_id)
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


@dataclass
class LessonWatchStatus:
    lesson_slug: str
    lesson_title: str
    position: int
    progress: WatchProgressData


@dataclass
class CourseWatchStatus:
    gate_met: bool
    lessons: list[LessonWatchStatus]


def course_watch_status(
    db: Session, course: Course, viewer_id: uuid.UUID, user_id: int | None = None
) -> CourseWatchStatus:
    lesson_statuses = [
        LessonWatchStatus(
            lesson_slug=lesson.slug,
            lesson_title=lesson.title,
            position=lesson.position,
            progress=get_progress(db, lesson, viewer_id, user_id),
        )
        for lesson in course.lessons
        if lesson.is_published
    ]
    # A lesson with no duration is already reported as unlocked by
    # get_progress, so the gate only ever waits on lessons that have
    # something to watch.
    gate_met = all(status.progress.unlocked for status in lesson_statuses)
    return CourseWatchStatus(gate_met=gate_met, lessons=lesson_statuses)
