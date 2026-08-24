from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.course import Course
from app.models.learning_objective import LearningObjective
from app.models.lesson import Lesson
from app.models.question import Question
from app.services import sponsor_profile as sponsor_profile_service


@dataclass
class SMESummary:
    name: str
    credentials: str


@dataclass
class CourseListItem:
    id: int
    slug: str
    title: str
    description: str
    has_thumbnail: bool
    lesson_count: int


@dataclass
class CourseWithLessons:
    id: int
    slug: str
    title: str
    description: str
    has_thumbnail: bool
    program_level: str
    field_of_study: str
    prerequisites: str | None
    advance_preparation: str | None
    learning_objectives: list["LearningObjective"]
    lessons: list[Lesson]
    reviewed_at: datetime | None
    developer: SMESummary | None
    reviewer: SMESummary | None
    credit_award: Decimal | None
    expires_on: date | None
    # Feature 027: a live read, not a snapshot - unlike a certificate, this
    # page describes the sponsor's current state, not a historical claim, so
    # there is nothing here to freeze. See the pre-enrollment disclosure
    # reasoning in current-feature.md's frontend task 3.
    sponsor_registry_status: str


@dataclass
class LessonSegmentData:
    id: int
    slug: str
    title: str
    description: str
    duration_seconds: int | None
    video_key: str | None
    has_thumbnail: bool
    position: int
    course_slug: str
    course_title: str
    previous_lesson_slug: str | None
    next_lesson_slug: str | None


def list_published(db: Session) -> list[CourseListItem]:
    # 9.02.2: an expired course "should stop listing publicly but should not
    # be force-unpublished" - see current-feature.md, Part 2. It stays
    # is_published=True and reachable at its own URL; only the catalog
    # listing excludes it.
    today = datetime.now(timezone.utc).date()
    stmt = (
        select(Course, func.count(Lesson.id))
        .outerjoin(Lesson, and_(Lesson.course_id == Course.id, Lesson.is_published.is_(True)))
        .where(
            Course.is_published.is_(True),
            or_(Course.expires_on.is_(None), Course.expires_on >= today),
        )
        .group_by(Course.id)
        .order_by(Course.id)
    )
    rows = db.execute(stmt).all()
    return [
        CourseListItem(
            id=course.id,
            slug=course.slug,
            title=course.title,
            description=course.description,
            has_thumbnail=course.has_thumbnail,
            lesson_count=lesson_count,
        )
        for course, lesson_count in rows
    ]


def get_by_slug(db: Session, slug: str) -> Course | None:
    stmt = select(Course).where(Course.slug == slug, Course.is_published.is_(True))
    return db.execute(stmt).scalar_one_or_none()


def get_with_lessons(db: Session, slug: str) -> CourseWithLessons | None:
    stmt = (
        select(Course)
        .where(Course.slug == slug, Course.is_published.is_(True))
        .options(
            selectinload(Course.lessons),
            selectinload(Course.learning_objectives),
            selectinload(Course.developer),
            selectinload(Course.reviewer),
        )
    )
    course = db.execute(stmt).scalar_one_or_none()
    if course is None:
        return None

    return CourseWithLessons(
        id=course.id,
        slug=course.slug,
        title=course.title,
        description=course.description,
        has_thumbnail=course.has_thumbnail,
        program_level=course.program_level,
        field_of_study=course.field_of_study,
        prerequisites=course.prerequisites,
        advance_preparation=course.advance_preparation,
        learning_objectives=course.learning_objectives,
        lessons=[lesson for lesson in course.lessons if lesson.is_published],
        reviewed_at=course.reviewed_at,
        developer=SMESummary(name=course.developer.name, credentials=course.developer.credentials)
        if course.developer
        else None,
        reviewer=SMESummary(name=course.reviewer.name, credentials=course.reviewer.credentials)
        if course.reviewer
        else None,
        credit_award=course.credit_award,
        expires_on=course.expires_on,
        sponsor_registry_status=sponsor_profile_service.get_sponsor_profile(db).registry_status,
    )


def get_lesson_in_course(db: Session, course_slug: str, lesson_slug: str) -> LessonSegmentData | None:
    stmt = (
        select(Course)
        .where(Course.slug == course_slug, Course.is_published.is_(True))
        .options(selectinload(Course.lessons))
    )
    course = db.execute(stmt).scalar_one_or_none()
    if course is None:
        return None

    published_lessons = [lesson for lesson in course.lessons if lesson.is_published]
    index = next((i for i, lesson in enumerate(published_lessons) if lesson.slug == lesson_slug), None)
    if index is None:
        return None

    lesson = published_lessons[index]
    previous_lesson = published_lessons[index - 1] if index > 0 else None
    next_lesson = published_lessons[index + 1] if index + 1 < len(published_lessons) else None

    return LessonSegmentData(
        id=lesson.id,
        slug=lesson.slug,
        title=lesson.title,
        description=lesson.description,
        duration_seconds=lesson.duration_seconds,
        video_key=lesson.video_key,
        has_thumbnail=lesson.has_thumbnail,
        position=lesson.position,
        course_slug=course.slug,
        course_title=course.title,
        previous_lesson_slug=previous_lesson.slug if previous_lesson else None,
        next_lesson_slug=next_lesson.slug if next_lesson else None,
    )


def get_published_lesson(db: Session, course_slug: str, lesson_slug: str) -> Lesson | None:
    stmt = (
        select(Lesson)
        .join(Course, Course.id == Lesson.course_id)
        .where(
            Course.slug == course_slug,
            Course.is_published.is_(True),
            Lesson.slug == lesson_slug,
            Lesson.is_published.is_(True),
        )
    )
    return db.execute(stmt).scalar_one_or_none()


def published_question_count(db: Session, course_id: int, kind: str | None = None) -> int:
    stmt = (
        select(func.count(Question.id))
        .select_from(Question)
        .join(Lesson, Lesson.id == Question.lesson_id)
        .where(Lesson.course_id == course_id, Lesson.is_published.is_(True))
    )
    if kind is not None:
        stmt = stmt.where(Question.kind == kind)
    return db.execute(stmt).scalar_one()
