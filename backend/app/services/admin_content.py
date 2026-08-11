import re
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.attempt import Attempt
from app.models.choice import Choice
from app.models.lesson import Lesson
from app.models.question import Question

REQUIRED_QUESTION_COUNT = 5
MIN_CHOICES_PER_QUESTION = 2


class LessonNotFoundError(Exception):
    """Raised when a lesson id does not match any lesson."""


class QuestionNotFoundError(Exception):
    """Raised when a question id does not match any question."""


class ChoiceNotFoundError(Exception):
    """Raised when a choice id does not match any choice."""


class SlugTakenError(Exception):
    """Raised when a lesson slug collides with an existing one."""


class LessonHasAttemptsError(Exception):
    """Raised when deleting a lesson that has completed attempts."""


class PublishValidationError(Exception):
    """Raised when publishing a lesson that fails validate_for_publish."""

    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


@dataclass
class LessonListItem:
    id: int
    slug: str
    title: str
    is_published: bool
    question_count: int
    has_video: bool


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.strip().lower()).strip("-")
    return slug or "lesson"


def _lesson_or_404(db: Session, lesson_id: int) -> Lesson:
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise LessonNotFoundError(f"Lesson {lesson_id} not found")
    return lesson


def _lesson_with_content_or_404(db: Session, lesson_id: int) -> Lesson:
    stmt = (
        select(Lesson)
        .where(Lesson.id == lesson_id)
        .options(selectinload(Lesson.questions).selectinload(Question.choices))
    )
    lesson = db.execute(stmt).scalar_one_or_none()
    if lesson is None:
        raise LessonNotFoundError(f"Lesson {lesson_id} not found")
    return lesson


def _question_or_404(db: Session, question_id: int) -> Question:
    stmt = (
        select(Question)
        .where(Question.id == question_id)
        .options(selectinload(Question.choices))
    )
    question = db.execute(stmt).scalar_one_or_none()
    if question is None:
        raise QuestionNotFoundError(f"Question {question_id} not found")
    return question


def _choice_or_404(db: Session, choice_id: int) -> Choice:
    choice = db.get(Choice, choice_id)
    if choice is None:
        raise ChoiceNotFoundError(f"Choice {choice_id} not found")
    return choice


def _check_slug_available(db: Session, slug: str, exclude_id: int | None = None) -> None:
    stmt = select(Lesson.id).where(Lesson.slug == slug)
    if exclude_id is not None:
        stmt = stmt.where(Lesson.id != exclude_id)
    if db.execute(stmt).scalar_one_or_none() is not None:
        raise SlugTakenError(f"Slug '{slug}' is already in use")


def list_lessons(db: Session) -> list[LessonListItem]:
    stmt = (
        select(Lesson, func.count(Question.id))
        .outerjoin(Question, Question.lesson_id == Lesson.id)
        .group_by(Lesson.id)
        .order_by(Lesson.id)
    )
    rows = db.execute(stmt).all()
    return [
        LessonListItem(
            id=lesson.id,
            slug=lesson.slug,
            title=lesson.title,
            is_published=lesson.is_published,
            question_count=question_count,
            has_video=lesson.video_key is not None,
        )
        for lesson, question_count in rows
    ]


def get_lesson(db: Session, lesson_id: int) -> Lesson:
    return _lesson_with_content_or_404(db, lesson_id)


def create_lesson(
    db: Session, title: str, slug: str | None, description: str, duration_seconds: int | None
) -> Lesson:
    final_slug = slug.strip().lower() if slug else slugify(title)
    _check_slug_available(db, final_slug)

    lesson = Lesson(
        title=title, slug=final_slug, description=description, duration_seconds=duration_seconds
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


def update_lesson(db: Session, lesson_id: int, updates: dict) -> Lesson:
    lesson = _lesson_or_404(db, lesson_id)

    if "slug" in updates and updates["slug"] is not None:
        new_slug = updates["slug"].strip().lower()
        if new_slug != lesson.slug:
            _check_slug_available(db, new_slug, exclude_id=lesson_id)
        updates["slug"] = new_slug

    for field, value in updates.items():
        setattr(lesson, field, value)

    db.commit()
    return _lesson_with_content_or_404(db, lesson_id)


def delete_lesson(db: Session, lesson_id: int) -> None:
    lesson = _lesson_or_404(db, lesson_id)

    completed_count = db.execute(
        select(func.count())
        .select_from(Attempt)
        .where(Attempt.lesson_id == lesson_id, Attempt.completed_at.is_not(None))
    ).scalar_one()
    if completed_count > 0:
        raise LessonHasAttemptsError(
            f"Lesson has {completed_count} completed attempt(s) and cannot be deleted"
        )

    db.delete(lesson)
    db.commit()


def publish_lesson(db: Session, lesson_id: int) -> Lesson:
    lesson = _lesson_with_content_or_404(db, lesson_id)
    errors = validate_for_publish(lesson)
    if errors:
        raise PublishValidationError(errors)

    lesson.is_published = True
    db.commit()
    return _lesson_with_content_or_404(db, lesson_id)


def check_publish(db: Session, lesson_id: int) -> list[str]:
    lesson = _lesson_with_content_or_404(db, lesson_id)
    return validate_for_publish(lesson)


def unpublish_lesson(db: Session, lesson_id: int) -> Lesson:
    lesson = _lesson_or_404(db, lesson_id)
    lesson.is_published = False
    db.commit()
    return _lesson_with_content_or_404(db, lesson_id)


def validate_for_publish(lesson: Lesson) -> list[str]:
    errors = []
    if not lesson.title.strip():
        errors.append("Title is required")
    if not lesson.slug.strip():
        errors.append("Slug is required")
    if not lesson.description.strip():
        errors.append("Description is required")
    if not lesson.video_key:
        errors.append("A video must be uploaded")
    if len(lesson.questions) != REQUIRED_QUESTION_COUNT:
        errors.append(
            f"Lesson must have exactly {REQUIRED_QUESTION_COUNT} questions, "
            f"has {len(lesson.questions)}"
        )
    for question in lesson.questions:
        if len(question.choices) < MIN_CHOICES_PER_QUESTION:
            errors.append(
                f"Question {question.position} needs at least "
                f"{MIN_CHOICES_PER_QUESTION} choices"
            )
        correct_count = sum(1 for choice in question.choices if choice.is_correct)
        if correct_count != 1:
            errors.append(f"Question {question.position} must have exactly one correct choice")
    return errors


def _renumber(db: Session, items: list) -> None:
    # Two-phase so no intermediate UPDATE collides with the (parent_id, position)
    # unique constraint: bump everything to a value nothing else holds, then
    # assign the final contiguous positions.
    for item in items:
        item.position = -item.id
    db.flush()
    for position, item in enumerate(items, start=1):
        item.position = position
    db.flush()


def create_question(db: Session, lesson_id: int, prompt: str) -> Question:
    _lesson_or_404(db, lesson_id)
    next_position = db.execute(
        select(func.coalesce(func.max(Question.position), 0)).where(Question.lesson_id == lesson_id)
    ).scalar_one()

    question = Question(lesson_id=lesson_id, prompt=prompt, position=next_position + 1)
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def update_question(db: Session, question_id: int, updates: dict) -> Question:
    question = _question_or_404(db, question_id)
    for field, value in updates.items():
        setattr(question, field, value)
    db.commit()
    return _question_or_404(db, question_id)


def delete_question(db: Session, question_id: int) -> None:
    question = _question_or_404(db, question_id)
    lesson_id = question.lesson_id
    db.delete(question)
    db.flush()

    remaining = list(
        db.execute(
            select(Question).where(Question.lesson_id == lesson_id).order_by(Question.position)
        ).scalars()
    )
    _renumber(db, remaining)
    db.commit()


def move_question(db: Session, question_id: int, direction: str) -> None:
    question = _question_or_404(db, question_id)
    ordered = list(
        db.execute(
            select(Question)
            .where(Question.lesson_id == question.lesson_id)
            .order_by(Question.position)
        ).scalars()
    )
    index = next(i for i, q in enumerate(ordered) if q.id == question_id)
    swap_with = index - 1 if direction == "up" else index + 1
    if 0 <= swap_with < len(ordered):
        ordered[index], ordered[swap_with] = ordered[swap_with], ordered[index]
        _renumber(db, ordered)
    db.commit()


def create_choice(db: Session, question_id: int, text: str, is_correct: bool) -> Choice:
    _question_or_404(db, question_id)
    next_position = db.execute(
        select(func.coalesce(func.max(Choice.position), 0)).where(Choice.question_id == question_id)
    ).scalar_one()

    choice = Choice(question_id=question_id, text=text, is_correct=is_correct, position=next_position + 1)
    db.add(choice)
    db.commit()
    db.refresh(choice)
    return choice


def update_choice(db: Session, choice_id: int, updates: dict) -> Choice:
    choice = _choice_or_404(db, choice_id)
    for field, value in updates.items():
        setattr(choice, field, value)
    db.commit()
    db.refresh(choice)
    return choice


def delete_choice(db: Session, choice_id: int) -> None:
    choice = _choice_or_404(db, choice_id)
    question_id = choice.question_id
    db.delete(choice)
    db.flush()

    remaining = list(
        db.execute(
            select(Choice).where(Choice.question_id == question_id).order_by(Choice.position)
        ).scalars()
    )
    _renumber(db, remaining)
    db.commit()


def move_choice(db: Session, choice_id: int, direction: str) -> None:
    choice = _choice_or_404(db, choice_id)
    ordered = list(
        db.execute(
            select(Choice).where(Choice.question_id == choice.question_id).order_by(Choice.position)
        ).scalars()
    )
    index = next(i for i, c in enumerate(ordered) if c.id == choice_id)
    swap_with = index - 1 if direction == "up" else index + 1
    if 0 <= swap_with < len(ordered):
        ordered[index], ordered[swap_with] = ordered[swap_with], ordered[index]
        _renumber(db, ordered)
    db.commit()


def set_correct_choice(db: Session, question_id: int, choice_id: int) -> None:
    question = _question_or_404(db, question_id)
    if not any(choice.id == choice_id for choice in question.choices):
        raise ChoiceNotFoundError(f"Choice {choice_id} does not belong to question {question_id}")

    for choice in question.choices:
        choice.is_correct = choice.id == choice_id
    db.commit()
