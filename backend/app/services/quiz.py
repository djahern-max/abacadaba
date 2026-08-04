from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.lesson import Lesson
from app.models.question import Question


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


def validate_question(question: Question) -> None:
    correct_choices = [choice for choice in question.choices if choice.is_correct]
    if len(correct_choices) != 1:
        raise ValueError(
            f"question {question.position!r} must have exactly one correct choice, "
            f"found {len(correct_choices)}"
        )
