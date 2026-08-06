import random
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.attempt import Attempt
from app.models.choice import Choice
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


def get_attempt_shuffle_seed(db: Session, attempt_id: uuid.UUID, lesson_id: int) -> int | None:
    stmt = select(Attempt.shuffle_seed).where(
        Attempt.public_id == attempt_id, Attempt.lesson_id == lesson_id
    )
    return db.execute(stmt).scalar_one_or_none()


def _rng(seed: int, salt: int) -> random.Random:
    # random.Random() only accepts a single hashable scalar, so the seed and
    # salt (0 for question order, a question id for that question's choice
    # order) are folded into one int rather than passed as a tuple.
    return random.Random(seed * 1_000_003 + salt)


def shuffle_questions(questions: list[Question], seed: int) -> list[Question]:
    shuffled = list(questions)
    _rng(seed, 0).shuffle(shuffled)
    return shuffled


def shuffle_choices(choices: list[Choice], seed: int, question_id: int) -> list[Choice]:
    shuffled = list(choices)
    _rng(seed, question_id).shuffle(shuffled)
    return shuffled
