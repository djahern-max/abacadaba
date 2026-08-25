import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.constants.program_kind import PROGRAM_KIND_CPE
from app.models.course import Course
from app.models.learning_objective import LearningObjective
from app.models.lesson import Lesson
from app.models.question import QUESTION_KIND_ASSESSMENT, Question
from app.models.user import User
from app.services import sponsor_profile as sponsor_profile_service
from app.services import watch as watch_service


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
    program_kind: str
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
    pass_ratio: Decimal
    assessment_question_count: int


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
    assessment_unlocked: bool
    assessment_outstanding_lesson: str | None


@dataclass
class AssessmentGateStatus:
    unlocked: bool
    outstanding_lesson_title: str | None


def get_assessment_gate_status(
    db: Session, course: Course, viewer_id: uuid.UUID, user: User | None
) -> AssessmentGateStatus:
    """Whether the assessment is reachable for this viewer, and what is
    outstanding if not.

    One implementation for a question two other places already answer
    separately: CourseDetail.jsx combines the admin's own `is_admin` with
    /watch-status's `gate_met`, and attempts_service.start_attempt bypasses
    the watch gate outright for an admin. This applies the same predicate so
    a segment page cannot tell an admin something the course page or the
    real enforcement disagrees with - see current-feature.md, "A thing to
    check rather than assume."
    """
    if user is not None and user.is_admin:
        return AssessmentGateStatus(unlocked=True, outstanding_lesson_title=None)
    status = watch_service.course_watch_status(db, course, viewer_id, user.id if user else None)
    if status.gate_met:
        return AssessmentGateStatus(unlocked=True, outstanding_lesson_title=None)
    outstanding = next(s for s in status.lessons if not s.progress.unlocked)
    return AssessmentGateStatus(unlocked=False, outstanding_lesson_title=outstanding.lesson_title)


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
        program_kind=course.program_kind,
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
        pass_ratio=course.pass_ratio,
        assessment_question_count=published_question_count(db, course.id, kind=QUESTION_KIND_ASSESSMENT),
    )


def get_lesson_in_course(
    db: Session, course_slug: str, lesson_slug: str, viewer_id: uuid.UUID, user: User | None
) -> LessonSegmentData | None:
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
    gate = get_assessment_gate_status(db, course, viewer_id, user)

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
        assessment_unlocked=gate.unlocked,
        assessment_outstanding_lesson=gate.outstanding_lesson_title,
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


def show_policy_footer(db: Session) -> bool:
    """Whether the site-wide footer should link the four policy pages.

    Derived, not a second flag - see current-feature.md, Part 6. A general
    course's own page links no policies (8.01.1 doesn't apply to it), so the
    footer earns its place only while at least one published course is
    actually offered as a CPE program. Publishing one CPE-presented course
    again brings the footer back with no configuration.
    """
    stmt = select(
        select(Course.id).where(Course.is_published.is_(True), Course.program_kind == PROGRAM_KIND_CPE).exists()
    )
    return db.execute(stmt).scalar_one()


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
