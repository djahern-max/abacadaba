import re
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.attempt import Attempt
from app.models.choice import Choice
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.question import Question

MIN_CHOICES_PER_QUESTION = 2


class CourseNotFoundError(Exception):
    """Raised when a course id does not match any course."""


class LessonNotFoundError(Exception):
    """Raised when a lesson id does not match any lesson."""


class QuestionNotFoundError(Exception):
    """Raised when a question id does not match any question."""


class ChoiceNotFoundError(Exception):
    """Raised when a choice id does not match any choice."""


class SlugTakenError(Exception):
    """Raised when a slug collides with an existing one."""


class CourseHasAttemptsError(Exception):
    """Raised when deleting a course that has completed attempts."""


class LessonHasAttemptsError(Exception):
    """Raised when deleting a lesson whose course has completed attempts."""


class PublishValidationError(Exception):
    """Raised when publishing a course that fails validate_for_publish."""

    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


@dataclass
class CourseListItem:
    id: int
    slug: str
    title: str
    is_published: bool
    lesson_count: int


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.strip().lower()).strip("-")
    return slug or "course"


def _check_slug_available(db: Session, model, slug: str, exclude_id: int | None = None) -> None:
    stmt = select(model.id).where(model.slug == slug)
    if exclude_id is not None:
        stmt = stmt.where(model.id != exclude_id)
    if db.execute(stmt).scalar_one_or_none() is not None:
        raise SlugTakenError(f"Slug '{slug}' is already in use")


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


# --- courses ---------------------------------------------------------------


def _course_or_404(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise CourseNotFoundError(f"Course {course_id} not found")
    return course


def _course_with_content_or_404(db: Session, course_id: int) -> Course:
    stmt = (
        select(Course)
        .where(Course.id == course_id)
        .options(selectinload(Course.lessons).selectinload(Lesson.questions).selectinload(Question.choices))
    )
    course = db.execute(stmt).scalar_one_or_none()
    if course is None:
        raise CourseNotFoundError(f"Course {course_id} not found")
    return course


def list_courses(db: Session) -> list[CourseListItem]:
    stmt = (
        select(Course, func.count(Lesson.id))
        .outerjoin(Lesson, Lesson.course_id == Course.id)
        .group_by(Course.id)
        .order_by(Course.id)
    )
    rows = db.execute(stmt).all()
    return [
        CourseListItem(id=course.id, slug=course.slug, title=course.title, is_published=course.is_published, lesson_count=lesson_count)
        for course, lesson_count in rows
    ]


def get_course(db: Session, course_id: int) -> Course:
    return _course_with_content_or_404(db, course_id)


def create_course(db: Session, title: str, slug: str | None, description: str) -> Course:
    final_slug = slug.strip().lower() if slug else slugify(title)
    _check_slug_available(db, Course, final_slug)

    course = Course(title=title, slug=final_slug, description=description)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def update_course(db: Session, course_id: int, updates: dict) -> Course:
    course = _course_or_404(db, course_id)

    if "slug" in updates and updates["slug"] is not None:
        new_slug = updates["slug"].strip().lower()
        if new_slug != course.slug:
            _check_slug_available(db, Course, new_slug, exclude_id=course_id)
        updates["slug"] = new_slug

    for field, value in updates.items():
        setattr(course, field, value)

    db.commit()
    return _course_with_content_or_404(db, course_id)


def delete_course(db: Session, course_id: int) -> None:
    course = _course_or_404(db, course_id)

    completed_count = db.execute(
        select(func.count())
        .select_from(Attempt)
        .where(Attempt.course_id == course_id, Attempt.completed_at.is_not(None))
    ).scalar_one()
    if completed_count > 0:
        raise CourseHasAttemptsError(
            f"Course has {completed_count} completed attempt(s) and cannot be deleted"
        )

    db.delete(course)
    db.commit()


def publish_course(db: Session, course_id: int) -> Course:
    course = _course_with_content_or_404(db, course_id)
    errors = validate_for_publish(course)
    if errors:
        raise PublishValidationError(errors)

    # validate_for_publish already required every lesson to have a video and
    # at least one well-formed question, so publishing the course publishes
    # its lessons with it - there is no separate per-lesson publish action.
    course.is_published = True
    for lesson in course.lessons:
        lesson.is_published = True
    db.commit()
    return _course_with_content_or_404(db, course_id)


def check_publish_course(db: Session, course_id: int) -> list[str]:
    course = _course_with_content_or_404(db, course_id)
    return validate_for_publish(course)


def unpublish_course(db: Session, course_id: int) -> Course:
    course = _course_or_404(db, course_id)
    course.is_published = False
    db.commit()
    return _course_with_content_or_404(db, course_id)


def validate_for_publish(course: Course) -> list[str]:
    errors = []
    if not course.title.strip():
        errors.append("Title is required")
    if not course.slug.strip():
        errors.append("Slug is required")
    if not course.description.strip():
        errors.append("Description is required")
    if not course.lessons:
        errors.append("Course must have at least one lesson")

    for lesson in course.lessons:
        if not lesson.video_key:
            errors.append(f"Lesson '{lesson.title}' must have a video")
        if not lesson.questions:
            errors.append(f"Lesson '{lesson.title}' must have at least one question")
        for question in lesson.questions:
            if len(question.choices) < MIN_CHOICES_PER_QUESTION:
                errors.append(
                    f"Lesson '{lesson.title}' question {question.position} needs at least "
                    f"{MIN_CHOICES_PER_QUESTION} choices"
                )
            correct_count = sum(1 for choice in question.choices if choice.is_correct)
            if correct_count != 1:
                errors.append(
                    f"Lesson '{lesson.title}' question {question.position} must have exactly one correct choice"
                )
    return errors


# --- lessons -----------------------------------------------------------------


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


def get_lesson(db: Session, lesson_id: int) -> Lesson:
    return _lesson_with_content_or_404(db, lesson_id)


def create_lesson(
    db: Session, course_id: int, title: str, slug: str | None, description: str, duration_seconds: int | None
) -> Lesson:
    _course_or_404(db, course_id)
    final_slug = slug.strip().lower() if slug else slugify(title)
    _check_slug_available(db, Lesson, final_slug)

    next_position = db.execute(
        select(func.coalesce(func.max(Lesson.position), 0)).where(Lesson.course_id == course_id)
    ).scalar_one()

    lesson = Lesson(
        course_id=course_id,
        position=next_position + 1,
        title=title,
        slug=final_slug,
        description=description,
        duration_seconds=duration_seconds,
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
            _check_slug_available(db, Lesson, new_slug, exclude_id=lesson_id)
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
        .where(Attempt.course_id == lesson.course_id, Attempt.completed_at.is_not(None))
    ).scalar_one()
    if completed_count > 0:
        raise LessonHasAttemptsError(
            f"This lesson's course has {completed_count} completed attempt(s) and cannot be edited"
        )

    course_id = lesson.course_id
    db.delete(lesson)
    db.flush()

    remaining = list(
        db.execute(select(Lesson).where(Lesson.course_id == course_id).order_by(Lesson.position)).scalars()
    )
    _renumber(db, remaining)
    db.commit()


def move_lesson(db: Session, lesson_id: int, direction: str) -> None:
    lesson = _lesson_or_404(db, lesson_id)
    ordered = list(
        db.execute(
            select(Lesson).where(Lesson.course_id == lesson.course_id).order_by(Lesson.position)
        ).scalars()
    )
    index = next(i for i, l in enumerate(ordered) if l.id == lesson_id)
    swap_with = index - 1 if direction == "up" else index + 1
    if 0 <= swap_with < len(ordered):
        ordered[index], ordered[swap_with] = ordered[swap_with], ordered[index]
        _renumber(db, ordered)
    db.commit()


# --- questions and choices ---------------------------------------------------


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
