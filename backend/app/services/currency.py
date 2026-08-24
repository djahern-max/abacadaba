from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.currency import DUE_SOON_WINDOW_DAYS, REVIEW_WINDOW_DAYS
from app.models.course import Course


@dataclass
class ReviewCurrencyRow:
    course_id: int
    title: str
    is_published: bool
    reviewed_at: datetime
    review_cycle: str
    due_at: datetime
    days_overdue: int  # positive once past due_at; the sort key, worst first


@dataclass
class PublishedButEditedRow:
    course_id: int
    title: str
    reviewed_at: datetime
    content_updated_at: datetime
    days_since_edit: int  # days content has been unreviewed, worst first


@dataclass
class ExpirationRow:
    course_id: int
    title: str
    is_published: bool
    expires_on: date
    days_until_expiry: int  # negative once past expires_on, worst (most negative) first


@dataclass
class CurrencyDashboardData:
    overdue_review: list[ReviewCurrencyRow]
    due_soon: list[ReviewCurrencyRow]
    published_but_edited: list[PublishedButEditedRow]
    expired_or_expiring: list[ExpirationRow]


def _review_due_at(reviewed_at: datetime, review_cycle: str) -> datetime:
    return reviewed_at + timedelta(days=REVIEW_WINDOW_DAYS[review_cycle])


def _reviewed_courses(db: Session) -> list[Course]:
    stmt = select(Course).where(Course.reviewed_at.is_not(None))
    return list(db.execute(stmt).scalars())


def overdue_review(db: Session, now: datetime | None = None) -> list[ReviewCurrencyRow]:
    now = now or datetime.now(timezone.utc)
    rows = []
    for course in _reviewed_courses(db):
        due_at = _review_due_at(course.reviewed_at, course.review_cycle)
        if due_at < now:
            rows.append(
                ReviewCurrencyRow(
                    course_id=course.id,
                    title=course.title,
                    is_published=course.is_published,
                    reviewed_at=course.reviewed_at,
                    review_cycle=course.review_cycle,
                    due_at=due_at,
                    days_overdue=(now - due_at).days,
                )
            )
    return sorted(rows, key=lambda row: row.days_overdue, reverse=True)


def due_soon(db: Session, now: datetime | None = None) -> list[ReviewCurrencyRow]:
    # 4.01's window, not yet lapsed - "an annual review that surfaces the day
    # it lapses has already lapsed," so this excludes anything overdue_review
    # already caught above.
    now = now or datetime.now(timezone.utc)
    cutoff = now + timedelta(days=DUE_SOON_WINDOW_DAYS)
    rows = []
    for course in _reviewed_courses(db):
        due_at = _review_due_at(course.reviewed_at, course.review_cycle)
        if now <= due_at <= cutoff:
            rows.append(
                ReviewCurrencyRow(
                    course_id=course.id,
                    title=course.title,
                    is_published=course.is_published,
                    reviewed_at=course.reviewed_at,
                    review_cycle=course.review_cycle,
                    due_at=due_at,
                    days_overdue=(now - due_at).days,  # negative: days until due
                )
            )
    # Worst first: soonest due (smallest days-until-due) leads.
    return sorted(rows, key=lambda row: row.due_at)


def published_but_edited(db: Session) -> list[PublishedButEditedRow]:
    # 4.02's gap, feature 021 recorded and left open by design: a published
    # course whose content was edited after its last review keeps serving
    # participants unreviewed content until someone re-reviews it. This is
    # that mitigation - reporting the state, not preventing it.
    stmt = select(Course).where(
        Course.is_published.is_(True),
        Course.reviewed_at.is_not(None),
        Course.content_updated_at > Course.reviewed_at,
    )
    rows = [
        PublishedButEditedRow(
            course_id=course.id,
            title=course.title,
            reviewed_at=course.reviewed_at,
            content_updated_at=course.content_updated_at,
            days_since_edit=(course.content_updated_at - course.reviewed_at).days,
        )
        for course in db.execute(stmt).scalars()
    ]
    return sorted(rows, key=lambda row: row.days_since_edit, reverse=True)


def expired_or_expiring(db: Session, today: date | None = None) -> list[ExpirationRow]:
    today = today or datetime.now(timezone.utc).date()
    cutoff = today + timedelta(days=DUE_SOON_WINDOW_DAYS)
    stmt = select(Course).where(Course.expires_on.is_not(None), Course.expires_on <= cutoff)
    rows = [
        ExpirationRow(
            course_id=course.id,
            title=course.title,
            is_published=course.is_published,
            expires_on=course.expires_on,
            days_until_expiry=(course.expires_on - today).days,
        )
        for course in db.execute(stmt).scalars()
    ]
    # Worst first: already-expired (most negative) leads.
    return sorted(rows, key=lambda row: row.days_until_expiry)


def get_dashboard(db: Session) -> CurrencyDashboardData:
    return CurrencyDashboardData(
        overdue_review=overdue_review(db),
        due_soon=due_soon(db),
        published_but_edited=published_but_edited(db),
        expired_or_expiring=expired_or_expiring(db),
    )
