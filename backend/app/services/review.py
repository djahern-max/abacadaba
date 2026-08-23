import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.question import QUESTION_KIND_REVIEW, Question
from app.models.review_response import ReviewResponse
from app.services import courses as courses_service
from app.services.identity import identity_filter


class QuestionNotFoundError(Exception):
    """Raised when a review question does not belong to this lesson."""


class InvalidChoiceError(Exception):
    """Raised when a choice_id does not belong to the question being answered."""


@dataclass
class ReviewAnswerResult:
    correct: bool
    feedback: str | None


def get_review_questions(db: Session, course_slug: str, lesson_slug: str) -> list[Question] | None:
    """The segment's review questions, in position order. None if the
    course/lesson isn't published - a 404 upstream, same as every other
    lesson-scoped endpoint in app/routers/courses.py."""
    lesson = courses_service.get_published_lesson(db, course_slug, lesson_slug)
    if lesson is None:
        return None

    stmt = (
        select(Question)
        .where(Question.lesson_id == lesson.id, Question.kind == QUESTION_KIND_REVIEW)
        .options(selectinload(Question.choices))
        .order_by(Question.position)
    )
    return list(db.execute(stmt).scalars().all())


def _find_question(db: Session, course_slug: str, lesson_slug: str, question_id: int) -> Question:
    lesson = courses_service.get_published_lesson(db, course_slug, lesson_slug)
    if lesson is None:
        raise QuestionNotFoundError(f"Question {question_id} not found for this lesson")

    stmt = (
        select(Question)
        .where(
            Question.id == question_id,
            Question.lesson_id == lesson.id,
            Question.kind == QUESTION_KIND_REVIEW,
        )
        .options(selectinload(Question.choices))
    )
    question = db.execute(stmt).scalar_one_or_none()
    if question is None:
        raise QuestionNotFoundError(f"Question {question_id} not found for this lesson")
    return question


def record_answer(
    db: Session,
    course_slug: str,
    lesson_slug: str,
    question_id: int,
    choice_id: int,
    viewer_id: uuid.UUID,
    user_id: int | None,
) -> ReviewAnswerResult:
    question = _find_question(db, course_slug, lesson_slug, question_id)

    chosen = next((choice for choice in question.choices if choice.id == choice_id), None)
    if chosen is None:
        raise InvalidChoiceError(f"Choice {choice_id} does not belong to question {question_id}")

    # Re-answering overwrites - there is no score to protect (5.01.2.1 sets
    # no minimum passing rate for review questions), unlike the qualified
    # assessment's replay guard in app/services/attempts.py. This table never
    # touches attempts/attempt_answers - see app/models/review_response.py.
    existing = db.execute(
        select(ReviewResponse).where(
            ReviewResponse.question_id == question_id,
            identity_filter(ReviewResponse.user_id, ReviewResponse.viewer_id, viewer_id, user_id),
        )
    ).scalar_one_or_none()

    if existing is not None:
        existing.choice_id = choice_id
        existing.is_correct = chosen.is_correct
        existing.answered_at = datetime.now(timezone.utc)
    else:
        db.add(
            ReviewResponse(
                question_id=question_id,
                viewer_id=viewer_id,
                user_id=user_id,
                choice_id=choice_id,
                is_correct=chosen.is_correct,
            )
        )
    db.commit()

    return ReviewAnswerResult(correct=chosen.is_correct, feedback=question.feedback)
