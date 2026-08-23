"""The 2026 word-count CPE credit formula (Section 7 Paragraphs 7.01,
7.02.6, 7.02.7 of docs/2026-Statement-on-Standards-for-CPE-Programs.pdf).

compute() is pure and read-only. store() is the only function here that
writes, and only when called explicitly (see admin_content.update_course
call below) - never from a content edit, so a course's credit doesn't
change while an author is mid-edit.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import ROUND_FLOOR, Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.constants.credit import (
    CREDIT_FORMULA_VERSION,
    MINUTES_PER_CREDIT,
    MINUTES_PER_QUESTION,
    WORDS_PER_MINUTE,
)
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.question import Question
from app.services import admin_content


@dataclass
class CreditBreakdown:
    course_id: int
    word_count: int | None
    av_seconds: int | None
    question_count: int | None
    word_term_minutes: Decimal | None
    av_term_minutes: Decimal | None
    question_term_minutes: Decimal | None
    raw_minutes: Decimal | None
    raw_credit: Decimal | None
    award: Decimal | None
    formula_version: str | None
    computed_at: datetime | None


def round_down(raw: Decimal) -> Decimal:
    """Round down to the finest legal self study increment, one-fifth
    (Section 7.01) - never up, per 7.02.6's closing sentence. State boards
    differ on which increments a CPA may actually claim (one-fifth vs
    one-half); superCPE, which will issue real NASBA-registered credit,
    will likely need a per-jurisdiction rounding policy. Not built here."""
    return (raw * 5).to_integral_value(rounding=ROUND_FLOOR) / 5


def compute(db: Session, course_id: int) -> CreditBreakdown:
    course = db.get(Course, course_id)
    if course is None:
        raise admin_content.CourseNotFoundError(f"Course {course_id} not found")

    lessons = list(db.execute(select(Lesson).where(Lesson.course_id == course_id)).scalars())

    word_count = 0
    av_seconds = 0
    for lesson in lessons:
        if lesson.av_is_additional_learning:
            av_seconds += lesson.duration_seconds or 0
        else:
            word_count += lesson.word_count

    # Every question on the course counts - review questions above the
    # minimum, exercises, and qualified assessment questions alike (7.02.6).
    # Deliberately every one of the course's lessons here, not
    # courses_service.published_question_count's is_published-gated count:
    # a course publishes every one of its lessons atomically in one step
    # (admin_content.publish_course), so before a course's first-ever
    # publish no lesson is published yet - a gated count would make credit
    # permanently zero and the course would never be able to clear its own
    # publish gate. When feature 023 splits review from assessment
    # questions, this must keep counting both; only the participant-facing
    # assessment endpoint should ever filter to assessment-only.
    question_count = db.execute(
        select(func.count(Question.id)).select_from(Question).join(Lesson).where(Lesson.course_id == course_id)
    ).scalar_one()

    word_term = Decimal(word_count) / WORDS_PER_MINUTE
    av_term = Decimal(av_seconds) / 60
    question_term = Decimal(question_count) * MINUTES_PER_QUESTION
    raw_minutes = word_term + av_term + question_term
    raw_credit = raw_minutes / MINUTES_PER_CREDIT
    award = round_down(raw_credit)

    return CreditBreakdown(
        course_id=course_id,
        word_count=word_count,
        av_seconds=av_seconds,
        question_count=question_count,
        word_term_minutes=word_term,
        av_term_minutes=av_term,
        question_term_minutes=question_term,
        raw_minutes=raw_minutes,
        raw_credit=raw_credit,
        award=award,
        formula_version=CREDIT_FORMULA_VERSION,
        computed_at=None,
    )


def store(db: Session, course_id: int) -> CreditBreakdown:
    breakdown = compute(db, course_id)
    computed_at = datetime.now(timezone.utc)
    admin_content.update_course(
        db,
        course_id,
        {
            "credit_award": breakdown.award,
            "credit_raw_minutes": breakdown.raw_minutes,
            "credit_word_count": breakdown.word_count,
            "credit_av_seconds": breakdown.av_seconds,
            "credit_question_count": breakdown.question_count,
            "credit_formula_version": breakdown.formula_version,
            "credit_computed_at": computed_at,
        },
    )
    breakdown.computed_at = computed_at
    return breakdown


def from_stored(course: Course) -> CreditBreakdown:
    """The last-stored breakdown, read straight off the course row - no
    recomputation. Used by the GET endpoint; POST always recomputes."""
    if course.credit_computed_at is None:
        return CreditBreakdown(
            course_id=course.id,
            word_count=None,
            av_seconds=None,
            question_count=None,
            word_term_minutes=None,
            av_term_minutes=None,
            question_term_minutes=None,
            raw_minutes=None,
            raw_credit=None,
            award=None,
            formula_version=None,
            computed_at=None,
        )

    word_term = Decimal(course.credit_word_count) / WORDS_PER_MINUTE
    av_term = Decimal(course.credit_av_seconds) / 60
    question_term = Decimal(course.credit_question_count) * MINUTES_PER_QUESTION
    raw_credit = course.credit_raw_minutes / MINUTES_PER_CREDIT

    return CreditBreakdown(
        course_id=course.id,
        word_count=course.credit_word_count,
        av_seconds=course.credit_av_seconds,
        question_count=course.credit_question_count,
        word_term_minutes=word_term,
        av_term_minutes=av_term,
        question_term_minutes=question_term,
        raw_minutes=course.credit_raw_minutes,
        raw_credit=raw_credit,
        award=course.credit_award,
        formula_version=course.credit_formula_version,
        computed_at=course.credit_computed_at,
    )
