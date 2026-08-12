import math
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.attempt import Attempt
from app.models.attempt_answer import AttemptAnswer
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.question import Question
from app.models.user import User
from app.services import courses as courses_service
from app.services import watch as watch_service

# A five question course keeps today's behaviour exactly: ceil(0.8 * 5) == 4.
PASS_RATIO = 0.8
MAX_SHUFFLE_SEED = 2_147_483_647


class AttemptNotFoundError(Exception):
    """Raised when a public_id does not match any attempt."""


class WatchRequirementNotMetError(Exception):
    """Raised when starting an attempt before every segment has been watched."""

    def __init__(self, lesson_slug: str, lesson_title: str, remaining_seconds: int):
        super().__init__(
            f"Watch {remaining_seconds} more second(s) of '{lesson_title}' before starting the assessment"
        )
        self.lesson_slug = lesson_slug
        self.lesson_title = lesson_title
        self.remaining_seconds = remaining_seconds


class MaxAttemptsExceededError(Exception):
    """Raised when a viewer has already used up their allotted attempts."""

    def __init__(self, max_attempts: int):
        super().__init__(f"You've used all {max_attempts} of your attempts for this course")
        self.max_attempts = max_attempts


class RetakeCooldownError(Exception):
    """Raised when a retake is attempted before the cooldown has elapsed."""

    def __init__(self, retry_at: datetime):
        super().__init__(f"You can retake this assessment after {retry_at.isoformat()}")
        self.retry_at = retry_at


class AttemptCompleteError(Exception):
    """Raised when trying to answer within an attempt that already finished."""


class AttemptNotCompleteError(Exception):
    """Raised when reading a result for an attempt that hasn't finished."""


class QuestionNotFoundError(Exception):
    """Raised when a question does not belong to the attempt's course."""


class InvalidChoiceError(Exception):
    """Raised when a choice_id does not belong to the question being answered."""


class DuplicateAnswerError(Exception):
    """Raised when a question has already been answered within this attempt."""


@dataclass
class AttemptStartResult:
    attempt_id: uuid.UUID
    course_slug: str
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
    course_slug: str
    course_title: str
    score: int
    question_count: int
    passed: bool
    completed_at: datetime
    certificate_code: str | None


@dataclass
class UserAttemptData:
    attempt_id: uuid.UUID
    course_title: str
    course_slug: str
    score: int
    passed: bool
    completed_at: datetime
    certificate_code: str | None


def _pass_threshold(question_count: int) -> int:
    return math.ceil(PASS_RATIO * question_count)


def _completed_attempts_count(db: Session, course_id: int, user_id: int) -> int:
    stmt = select(func.count()).select_from(Attempt).where(
        Attempt.course_id == course_id,
        Attempt.completed_at.is_not(None),
        Attempt.user_id == user_id,
    )
    return db.execute(stmt).scalar_one()


def _most_recent_completed_at(db: Session, course_id: int, user_id: int) -> datetime | None:
    stmt = select(func.max(Attempt.completed_at)).where(
        Attempt.course_id == course_id,
        Attempt.completed_at.is_not(None),
        Attempt.user_id == user_id,
    )
    return db.execute(stmt).scalar()


def _enforce_retake_policy(db: Session, course: Course, user_id: int) -> None:
    if course.max_attempts is not None:
        completed = _completed_attempts_count(db, course.id, user_id)
        if completed >= course.max_attempts:
            raise MaxAttemptsExceededError(course.max_attempts)

    if course.retake_cooldown_minutes > 0:
        last_completed_at = _most_recent_completed_at(db, course.id, user_id)
        if last_completed_at is not None:
            retry_at = last_completed_at + timedelta(minutes=course.retake_cooldown_minutes)
            if datetime.now(timezone.utc) < retry_at:
                raise RetakeCooldownError(retry_at)


def start_attempt(db: Session, slug: str, user: User, viewer_id: uuid.UUID) -> AttemptStartResult | None:
    stmt = (
        select(Course)
        .where(Course.slug == slug, Course.is_published.is_(True))
        .options(selectinload(Course.lessons))
    )
    course = db.execute(stmt).scalar_one_or_none()
    if course is None:
        return None

    question_count = courses_service.published_question_count(db, course.id)
    if question_count == 0:
        return None

    if not user.is_admin:
        status = watch_service.course_watch_status(db, course, viewer_id, user.id)
        if not status.gate_met:
            outstanding = next(s for s in status.lessons if not s.progress.unlocked)
            remaining = max(
                (outstanding.progress.required_seconds or 0) - outstanding.progress.watched_seconds, 0
            )
            raise WatchRequirementNotMetError(outstanding.lesson_slug, outstanding.lesson_title, remaining)
        _enforce_retake_policy(db, course, user.id)

    attempt = Attempt(
        course_id=course.id,
        user_id=user.id,
        viewer_id=viewer_id,
        shuffle_seed=random.randint(1, MAX_SHUFFLE_SEED),
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return AttemptStartResult(attempt_id=attempt.public_id, course_slug=course.slug, question_count=question_count)


def record_answer(db: Session, public_id: uuid.UUID, question_id: int, choice_id: int) -> AnswerResult:
    attempt = db.execute(select(Attempt).where(Attempt.public_id == public_id)).scalar_one_or_none()
    if attempt is None:
        raise AttemptNotFoundError(f"Attempt {public_id} not found")
    if attempt.completed_at is not None:
        raise AttemptCompleteError("This attempt is already complete")

    stmt = (
        select(Question)
        .join(Lesson, Lesson.id == Question.lesson_id)
        .where(Question.id == question_id, Lesson.course_id == attempt.course_id)
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

    question_count = courses_service.published_question_count(db, attempt.course_id)
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
        attempt.passed = score >= _pass_threshold(question_count)
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
        select(Attempt).where(Attempt.public_id == public_id).options(selectinload(Attempt.course))
    )
    attempt = db.execute(stmt).scalar_one_or_none()
    if attempt is None:
        raise AttemptNotFoundError(f"Attempt {public_id} not found")
    if attempt.completed_at is None:
        raise AttemptNotCompleteError("This attempt is not complete yet")

    return AttemptResultData(
        attempt_id=attempt.public_id,
        course_slug=attempt.course.slug,
        course_title=attempt.course.title,
        score=attempt.score,
        question_count=courses_service.published_question_count(db, attempt.course_id),
        passed=attempt.passed,
        completed_at=attempt.completed_at,
        certificate_code=attempt.certificate_code,
    )


def list_user_attempts(db: Session, user: User) -> list[UserAttemptData]:
    stmt = (
        select(Attempt)
        .where(Attempt.user_id == user.id, Attempt.completed_at.is_not(None))
        .options(selectinload(Attempt.course))
        .order_by(Attempt.completed_at.desc())
    )
    attempts = db.execute(stmt).scalars().all()
    return [
        UserAttemptData(
            attempt_id=attempt.public_id,
            course_title=attempt.course.title,
            course_slug=attempt.course.slug,
            score=attempt.score,
            passed=attempt.passed,
            completed_at=attempt.completed_at,
            certificate_code=attempt.certificate_code,
        )
        for attempt in attempts
    ]
