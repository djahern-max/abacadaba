from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.lesson import Lesson
from app.models.question import Question


class InvalidChoiceError(Exception):
    """Raised when a choice_id does not belong to the question being graded."""


@dataclass
class GradedAnswer:
    correct: bool
    correct_choice_id: int


def get_quiz_for_lesson(db: Session, slug: str) -> Lesson | None:
    stmt = (
        select(Lesson)
        .where(Lesson.slug == slug, Lesson.is_published.is_(True))
        .options(selectinload(Lesson.questions).selectinload(Question.choices))
    )
    lesson = db.execute(stmt).scalar_one_or_none()
    if lesson is None or not lesson.questions:
        return None
    return lesson


def grade_answer(db: Session, slug: str, question_id: int, choice_id: int) -> GradedAnswer | None:
    stmt = (
        select(Question)
        .join(Lesson)
        .where(
            Question.id == question_id,
            Lesson.slug == slug,
            Lesson.is_published.is_(True),
        )
        .options(selectinload(Question.choices))
    )
    question = db.execute(stmt).scalar_one_or_none()
    if question is None:
        return None

    chosen = next((choice for choice in question.choices if choice.id == choice_id), None)
    if chosen is None:
        raise InvalidChoiceError(f"Choice {choice_id} does not belong to question {question_id}")

    correct_choice = next(choice for choice in question.choices if choice.is_correct)
    return GradedAnswer(correct=chosen.is_correct, correct_choice_id=correct_choice.id)


def validate_question(question: Question) -> None:
    correct_choices = [choice for choice in question.choices if choice.is_correct]
    if len(correct_choices) != 1:
        raise ValueError(
            f"question {question.position!r} must have exactly one correct choice, "
            f"found {len(correct_choices)}"
        )
