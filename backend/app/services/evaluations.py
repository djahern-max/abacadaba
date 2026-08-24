import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.constants.evaluation_dimensions import DIMENSION_KEYS
from app.models.attempt import Attempt
from app.models.evaluation import Evaluation


class AttemptNotFoundError(Exception):
    """Raised when a public_id does not match any attempt."""


class AttemptNotCompleteError(Exception):
    """Raised when submitting an evaluation for an attempt that hasn't finished."""


class DuplicateEvaluationError(Exception):
    """Raised when an evaluation already exists for this attempt."""


@dataclass
class EvaluationData:
    attempt_id: uuid.UUID
    objectives_met: int | None
    prerequisites_appropriate: int | None
    materials_relevant: int | None
    time_allotted_appropriate: int | None
    instructor_effective: int | None
    comments: str | None
    submitted_at: datetime


@dataclass
class DimensionMeanData:
    key: str
    mean: float | None


@dataclass
class CourseSummaryData:
    response_count: int
    completed_attempts_count: int
    response_rate: float | None
    means: list[DimensionMeanData]


@dataclass
class CommentData:
    comments: str
    submitted_at: datetime


def _get_attempt(db: Session, public_id: uuid.UUID) -> Attempt:
    attempt = db.execute(select(Attempt).where(Attempt.public_id == public_id)).scalar_one_or_none()
    if attempt is None:
        raise AttemptNotFoundError(f"Attempt {public_id} not found")
    return attempt


def _to_data(evaluation: Evaluation, public_id: uuid.UUID) -> EvaluationData:
    return EvaluationData(
        attempt_id=public_id,
        objectives_met=evaluation.objectives_met,
        prerequisites_appropriate=evaluation.prerequisites_appropriate,
        materials_relevant=evaluation.materials_relevant,
        time_allotted_appropriate=evaluation.time_allotted_appropriate,
        instructor_effective=evaluation.instructor_effective,
        comments=evaluation.comments,
        submitted_at=evaluation.submitted_at,
    )


def submit(db: Session, public_id: uuid.UUID, ratings: dict[str, int | None], comments: str | None) -> EvaluationData:
    attempt = _get_attempt(db, public_id)
    if attempt.completed_at is None:
        raise AttemptNotCompleteError("This attempt is not complete yet")

    evaluation = Evaluation(attempt_id=attempt.id, comments=comments, **ratings)
    db.add(evaluation)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateEvaluationError(f"An evaluation was already submitted for attempt {public_id}") from exc

    db.commit()
    db.refresh(evaluation)
    return _to_data(evaluation, public_id)


def get_for_attempt(db: Session, public_id: uuid.UUID) -> EvaluationData | None:
    attempt = _get_attempt(db, public_id)
    evaluation = db.execute(select(Evaluation).where(Evaluation.attempt_id == attempt.id)).scalar_one_or_none()
    if evaluation is None:
        return None
    return _to_data(evaluation, public_id)


def course_summary(db: Session, course_id: int) -> CourseSummaryData:
    # One query: an outer join keeps every attempt in the denominator even
    # when it has no evaluation, so response_count, completed_attempts_count,
    # and every dimension's mean (which AVG already computes over non-null
    # values only) all fall out of a single pass over the joined rows.
    mean_columns = [func.avg(getattr(Evaluation, key)).label(key) for key in DIMENSION_KEYS]
    stmt = (
        select(
            func.count(func.distinct(Evaluation.id)).label("response_count"),
            func.count(func.distinct(Attempt.id)).filter(Attempt.completed_at.is_not(None)).label("completed_count"),
            *mean_columns,
        )
        .select_from(Attempt)
        .outerjoin(Evaluation, Evaluation.attempt_id == Attempt.id)
        .where(Attempt.course_id == course_id)
    )
    row = db.execute(stmt).one()

    response_rate = (row.response_count / row.completed_count) if row.completed_count else None
    means = [
        DimensionMeanData(key=key, mean=float(value) if (value := getattr(row, key)) is not None else None)
        for key in DIMENSION_KEYS
    ]

    return CourseSummaryData(
        response_count=row.response_count,
        completed_attempts_count=row.completed_count,
        response_rate=response_rate,
        means=means,
    )


def course_comments(db: Session, course_id: int) -> list[CommentData]:
    stmt = (
        select(Evaluation.comments, Evaluation.submitted_at)
        .join(Attempt, Attempt.id == Evaluation.attempt_id)
        .where(
            Attempt.course_id == course_id,
            Evaluation.comments.is_not(None),
            func.trim(Evaluation.comments) != "",
        )
        .order_by(Evaluation.submitted_at.desc())
    )
    rows = db.execute(stmt).all()
    return [CommentData(comments=row.comments, submitted_at=row.submitted_at) for row in rows]
