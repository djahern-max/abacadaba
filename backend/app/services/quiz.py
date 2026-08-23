import random
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.attempt import Attempt
from app.models.choice import Choice
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.question import QUESTION_KIND_ASSESSMENT, Question


@dataclass
class CourseQuiz:
    course_slug: str
    course_title: str
    questions: list[Question]


def get_quiz_for_course(db: Session, slug: str) -> CourseQuiz | None:
    stmt = (
        select(Course)
        .where(Course.slug == slug, Course.is_published.is_(True))
        .options(selectinload(Course.lessons).selectinload(Lesson.questions).selectinload(Question.choices))
    )
    course = db.execute(stmt).scalar_one_or_none()
    if course is None:
        return None

    # course.lessons is ordered by Lesson.position and each lesson's questions
    # by Question.position, so this comprehension already yields lesson-then-
    # question order without an extra sort. Feature 023: the qualified
    # assessment serves assessment questions only - review questions are
    # served separately, at segment boundaries (app/services/review.py).
    questions = [
        question
        for lesson in course.lessons
        if lesson.is_published
        for question in lesson.questions
        if question.kind == QUESTION_KIND_ASSESSMENT
    ]
    if not questions:
        return None
    return CourseQuiz(course_slug=course.slug, course_title=course.title, questions=questions)


def validate_question(question: Question) -> None:
    correct_choices = [choice for choice in question.choices if choice.is_correct]
    if len(correct_choices) != 1:
        raise ValueError(
            f"question {question.position!r} must have exactly one correct choice, "
            f"found {len(correct_choices)}"
        )


def get_attempt_shuffle_seed(db: Session, attempt_id: uuid.UUID, course_id: int) -> int | None:
    stmt = select(Attempt.shuffle_seed).where(
        Attempt.public_id == attempt_id, Attempt.course_id == course_id
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
