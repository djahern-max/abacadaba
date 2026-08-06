import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.attempt import Attempt
from app.models.attempt_answer import AttemptAnswer
from app.models.lesson import Lesson
from app.models.question import Question
from app.models.user import User
from app.services import watch as watch_service

PASS_THRESHOLD = 4
MAX_SHUFFLE_SEED = 2_147_483_647


class AttemptNotFoundError(Exception):
    """Raised when a public_id does not match any attempt."""


class WatchRequirementNotMetError(Exception):
    """Raised when starting an attempt before the watch gate is satisfied."""

    def __init__(self, remaining_seconds: int):
        super().__init__(f"Watch {remaining_seconds} more second(s) of the video before starting the quiz")
        self.remaining_seconds = remaining_seconds


class MaxAttemptsExceededError(Exception):
    """Raised when a viewer has already used up their allotted attempts."""

    def __init__(self, max_attempts: int):
        super().__init__(f"You've used all {max_attempts} of your attempts for this lesson")
        self.max_attempts = max_attempts


class RetakeCooldownError(Exception):
    """Raised when a retake is attempted before the cooldown has elapsed."""

    def __init__(self, retry_at: datetime):
        super().__init__(f"You can retake this quiz after {retry_at.isoformat()}")
        self.retry_at = retry_at


class AttemptCompleteError(Exception):
    """Raised when trying to answer within an attempt that already finished."""


class AttemptNotCompleteError(Exception):
    """Raised when reading a result for an attempt that hasn't finished."""


class QuestionNotFoundError(Exception):
    """Raised when a question does not belong to the attempt's lesson."""


class InvalidChoiceError(Exception):
    """Raised when a choice_id does not belong to the question being answered."""


class DuplicateAnswerError(Exception):
    """Raised when a question has already been answered within this attempt."""


@dataclass
class AttemptStartResult:
    attempt_id: uuid.UUID
    lesson_slug: str
    question_count: int


@dataclass
class AnswerResult:
    correct: bool
    correct_choice_id: int
    answered_count: int
    question_count: int


@dataclass
class AttemptResultData:
    attempt_id: uuid.UUID
    lesson_slug: str
    lesson_title: str
    score: int
    question_count: int
    passed: bool
    completed_at: datetime
    certificate_code: str | None


@dataclass
class UserAttemptData:
    attempt_id: uuid.UUID
    lesson_title: str
    lesson_slug: str
    score: int
    passed: bool
    completed_at: datetime
    certificate_code: str | None


def _question_count(db: Session, lesson_id: int) -> int:
    stmt = select(func.count()).select_from(Question).where(Question.lesson_id == lesson_id)
    return db.execute(stmt).scalar_one()


def _identity_filter(user_id: int | None, viewer_id: uuid.UUID | None):
    # A signed in user is identified by user_id regardless of which device or
    # cookie they're on; an anonymous viewer only has the cookie. Note this
    # means an anonymous viewer can clear their cookie to reset both the
    # cooldown and the attempt count — accepted for now, revisited if abused.
    if user_id is not None:
        return Attempt.user_id == user_id
    return Attempt.viewer_id == viewer_id


def _completed_attempts_count(db: Session, lesson_id: int, user_id: int | None, viewer_id: uuid.UUID | None) -> int:
    stmt = select(func.count()).select_from(Attempt).where(
        Attempt.lesson_id == lesson_id,
        Attempt.completed_at.is_not(None),
        _identity_filter(user_id, viewer_id),
    )
    return db.execute(stmt).scalar_one()


def _most_recent_completed_at(
    db: Session, lesson_id: int, user_id: int | None, viewer_id: uuid.UUID | None
) -> datetime | None:
    stmt = select(func.max(Attempt.completed_at)).where(
        Attempt.lesson_id == lesson_id,
        Attempt.completed_at.is_not(None),
        _identity_filter(user_id, viewer_id),
    )
    return db.execute(stmt).scalar()


def _enforce_retake_policy(
    db: Session, lesson: Lesson, user_id: int | None, viewer_id: uuid.UUID | None
) -> None:
    if lesson.max_attempts is not None:
        completed = _completed_attempts_count(db, lesson.id, user_id, viewer_id)
        if completed >= lesson.max_attempts:
            raise MaxAttemptsExceededError(lesson.max_attempts)

    if lesson.retake_cooldown_minutes > 0:
        last_completed_at = _most_recent_completed_at(db, lesson.id, user_id, viewer_id)
        if last_completed_at is not None:
            retry_at = last_completed_at + timedelta(minutes=lesson.retake_cooldown_minutes)
            if datetime.now(timezone.utc) < retry_at:
                raise RetakeCooldownError(retry_at)


def start_attempt(
    db: Session, slug: str, user: User | None = None, viewer_id: uuid.UUID | None = None
) -> AttemptStartResult | None:
    stmt = select(Lesson).where(Lesson.slug == slug, Lesson.is_published.is_(True))
    lesson = db.execute(stmt).scalar_one_or_none()
    if lesson is None:
        return None

    question_count = _question_count(db, lesson.id)
    if question_count == 0:
        return None

    is_admin = bool(user and user.is_admin)
    if not is_admin:
        if viewer_id is not None:
            progress = watch_service.get_progress(db, lesson, viewer_id, user.id if user else None)
            if not progress.unlocked:
                remaining = max((progress.required_seconds or 0) - progress.watched_seconds, 0)
                raise WatchRequirementNotMetError(remaining)
        _enforce_retake_policy(db, lesson, user.id if user else None, viewer_id)

    attempt = Attempt(
        lesson_id=lesson.id,
        user_id=user.id if user else None,
        viewer_id=viewer_id,
        shuffle_seed=random.randint(1, MAX_SHUFFLE_SEED),
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return AttemptStartResult(
        attempt_id=attempt.public_id, lesson_slug=lesson.slug, question_count=question_count
    )


def record_answer(db: Session, public_id: uuid.UUID, question_id: int, choice_id: int) -> AnswerResult:
    attempt = db.execute(select(Attempt).where(Attempt.public_id == public_id)).scalar_one_or_none()
    if attempt is None:
        raise AttemptNotFoundError(f"Attempt {public_id} not found")
    if attempt.completed_at is not None:
        raise AttemptCompleteError("This attempt is already complete")

    stmt = (
        select(Question)
        .where(Question.id == question_id, Question.lesson_id == attempt.lesson_id)
        .options(selectinload(Question.choices))
    )
    question = db.execute(stmt).scalar_one_or_none()
    if question is None:
        raise QuestionNotFoundError(f"Question {question_id} not found for this attempt")

    chosen = next((choice for choice in question.choices if choice.id == choice_id), None)
    if chosen is None:
        raise InvalidChoiceError(f"Choice {choice_id} does not belong to question {question_id}")

    db.add(
        AttemptAnswer(
            attempt_id=attempt.id,
            question_id=question_id,
            choice_id=choice_id,
            is_correct=chosen.is_correct,
        )
    )
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateAnswerError(f"Question {question_id} was already answered in this attempt") from exc

    question_count = _question_count(db, attempt.lesson_id)
    answered_count = db.execute(
        select(func.count()).select_from(AttemptAnswer).where(AttemptAnswer.attempt_id == attempt.id)
    ).scalar_one()

    if answered_count == question_count:
        score = db.execute(
            select(func.count())
            .select_from(AttemptAnswer)
            .where(AttemptAnswer.attempt_id == attempt.id, AttemptAnswer.is_correct.is_(True))
        ).scalar_one()
        attempt.score = score
        attempt.passed = score >= PASS_THRESHOLD
        attempt.completed_at = datetime.now(timezone.utc)

    db.commit()

    correct_choice_id = next(choice.id for choice in question.choices if choice.is_correct)
    return AnswerResult(
        correct=chosen.is_correct,
        correct_choice_id=correct_choice_id,
        answered_count=answered_count,
        question_count=question_count,
    )


def get_result(db: Session, public_id: uuid.UUID) -> AttemptResultData:
    stmt = (
        select(Attempt).where(Attempt.public_id == public_id).options(selectinload(Attempt.lesson))
    )
    attempt = db.execute(stmt).scalar_one_or_none()
    if attempt is None:
        raise AttemptNotFoundError(f"Attempt {public_id} not found")
    if attempt.completed_at is None:
        raise AttemptNotCompleteError("This attempt is not complete yet")

    return AttemptResultData(
        attempt_id=attempt.public_id,
        lesson_slug=attempt.lesson.slug,
        lesson_title=attempt.lesson.title,
        score=attempt.score,
        question_count=_question_count(db, attempt.lesson_id),
        passed=attempt.passed,
        completed_at=attempt.completed_at,
        certificate_code=attempt.certificate_code,
    )


def list_user_attempts(db: Session, user: User) -> list[UserAttemptData]:
    stmt = (
        select(Attempt)
        .where(Attempt.user_id == user.id, Attempt.completed_at.is_not(None))
        .options(selectinload(Attempt.lesson))
        .order_by(Attempt.completed_at.desc())
    )
    attempts = db.execute(stmt).scalars().all()
    return [
        UserAttemptData(
            attempt_id=attempt.public_id,
            lesson_title=attempt.lesson.title,
            lesson_slug=attempt.lesson.slug,
            score=attempt.score,
            passed=attempt.passed,
            completed_at=attempt.completed_at,
            certificate_code=attempt.certificate_code,
        )
        for attempt in attempts
    ]
