import random
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_CEILING, Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.attempt import Attempt
from app.models.attempt_answer import AttemptAnswer
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.question import QUESTION_KIND_ASSESSMENT, Question
from app.models.user import User
from app.services import courses as courses_service
from app.services import watch as watch_service

MAX_SHUFFLE_SEED = 2_147_483_647


class AttemptNotFoundError(Exception):
    """Raised when a public_id does not match any attempt."""


class CourseExpiredError(Exception):
    """Raised when starting an attempt on a course past its expiration date.

    9.02.2: expiry is a property of the course, not of the participant, so
    it's checked before authentication - see current-feature.md, Part 2.
    """

    def __init__(self, expires_on: date):
        super().__init__(
            f"This program expired on {expires_on.isoformat()} and is no longer accepting new attempts."
        )
        self.expires_on = expires_on


class NotAuthenticatedError(Exception):
    """Raised when starting an attempt while signed out, once the course's
    own expiry has already been checked - see CourseExpiredError."""


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
    # No correctness here, deliberately: under 6.01.2, with no test bank, the
    # application cannot know whether an in-progress attempt will pass, so
    # per-question feedback mid-attempt is feedback on a failed assessment
    # roughly half the time. See Part 4 of current-feature.md.
    answered_count: int
    question_count: int


@dataclass
class AnsweredQuestionResult:
    question_id: int
    prompt: str
    chosen_choice_id: int
    chosen_choice_text: str
    correct_choice_id: int
    correct_choice_text: str
    is_correct: bool
    # 6.01.2 sub-ii b: on assessments passed successfully, a sponsor may
    # provide feedback. This is only ever populated on a passed attempt - see
    # get_result, which never builds AnsweredQuestionResult for a fail.
    feedback: str | None


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
    # Per-question correctness. Populated only when passed - a failed
    # assessment gets a score and nothing else (6.01.2, no-test-bank arm:
    # "on a failed assessment, the CPE program sponsor may not provide
    # feedback to the test taker"). None rather than [] so the API shape
    # itself says "not available" instead of "available and empty".
    answers: list[AnsweredQuestionResult] | None


@dataclass
class UserAttemptData:
    attempt_id: uuid.UUID
    course_title: str
    course_slug: str
    score: int
    passed: bool
    completed_at: datetime
    certificate_code: str | None


def _pass_threshold(question_count: int, pass_ratio: Decimal) -> int:
    return int((pass_ratio * question_count).to_integral_value(rounding=ROUND_CEILING))


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


def start_attempt(
    db: Session, slug: str, user: User | None, viewer_id: uuid.UUID
) -> AttemptStartResult | None:
    stmt = (
        select(Course)
        .where(Course.slug == slug, Course.is_published.is_(True))
        .options(selectinload(Course.lessons))
    )
    course = db.execute(stmt).scalar_one_or_none()
    if course is None:
        return None

    # Feature 019 established authenticate, then gate, then policy. Expiry is
    # a property of the course, not of the participant, so it goes first -
    # telling someone how much video is left on a program they cannot take
    # is worse than useless. See current-feature.md, Part 2.
    if course.expires_on is not None and course.expires_on < datetime.now(timezone.utc).date():
        raise CourseExpiredError(course.expires_on)

    if user is None:
        raise NotAuthenticatedError("Sign in required")

    question_count = courses_service.published_question_count(db, course.id, kind=QUESTION_KIND_ASSESSMENT)
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
        .where(
            Question.id == question_id,
            Lesson.course_id == attempt.course_id,
            Question.kind == QUESTION_KIND_ASSESSMENT,
        )
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

    question_count = courses_service.published_question_count(db, attempt.course_id, kind=QUESTION_KIND_ASSESSMENT)
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
        attempt.passed = score >= _pass_threshold(question_count, attempt.course.pass_ratio)
        attempt.completed_at = datetime.now(timezone.utc)

    db.commit()

    return AnswerResult(answered_count=answered_count, question_count=question_count)


def _answered_question_results(db: Session, attempt_id: int) -> list[AnsweredQuestionResult]:
    stmt = (
        select(AttemptAnswer, Question)
        .join(Question, Question.id == AttemptAnswer.question_id)
        .where(AttemptAnswer.attempt_id == attempt_id)
        .options(selectinload(Question.choices))
        .order_by(Question.position)
    )
    rows = db.execute(stmt).all()

    results = []
    for answer, question in rows:
        chosen = next(choice for choice in question.choices if choice.id == answer.choice_id)
        correct = next(choice for choice in question.choices if choice.is_correct)
        results.append(
            AnsweredQuestionResult(
                question_id=question.id,
                prompt=question.prompt,
                chosen_choice_id=chosen.id,
                chosen_choice_text=chosen.text,
                correct_choice_id=correct.id,
                correct_choice_text=correct.text,
                is_correct=answer.is_correct,
                feedback=question.feedback,
            )
        )
    return results


def get_result(db: Session, public_id: uuid.UUID) -> AttemptResultData:
    stmt = (
        select(Attempt).where(Attempt.public_id == public_id).options(selectinload(Attempt.course))
    )
    attempt = db.execute(stmt).scalar_one_or_none()
    if attempt is None:
        raise AttemptNotFoundError(f"Attempt {public_id} not found")
    if attempt.completed_at is None:
        raise AttemptNotCompleteError("This attempt is not complete yet")

    # This is the no-test-bank arm of 6.01.2: feedback on a failed assessment
    # is not permitted; a passed one may show the breakdown at the sponsor's
    # discretion. A feature that adds a test bank would need to revisit this
    # branch - 6.01.2's test-bank arm allows feedback either way, gated on
    # bank size rather than on pass/fail. Computed only when needed - a
    # failed attempt never even builds the per-question data.
    answers = _answered_question_results(db, attempt.id) if attempt.passed else None

    return AttemptResultData(
        attempt_id=attempt.public_id,
        course_slug=attempt.course.slug,
        course_title=attempt.course.title,
        score=attempt.score,
        question_count=courses_service.published_question_count(
            db, attempt.course_id, kind=QUESTION_KIND_ASSESSMENT
        ),
        passed=attempt.passed,
        completed_at=attempt.completed_at,
        certificate_code=attempt.certificate_code,
        answers=answers,
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
