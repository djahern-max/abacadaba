"""Read-only reporting over completed attempts - the audit artifact a
sponsor produces on request (9.02). Aggregate SQL, one query, the same rule
feature 012 set for app/services/analytics.py.
"""
import csv
import io
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Iterator
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.attempt import Attempt
from app.models.course import Course
from app.models.user import User

CSV_HEADER = [
    "attempt_id",
    "course_title",
    "participant_name",
    "participant_email",
    "credit_award",
    "completed_at",
    "passed",
    "certificate_code",
]


@dataclass
class CompletionRow:
    attempt_id: UUID
    course_title: str
    participant_name: str | None
    participant_email: str | None
    credit_award: Decimal | None
    completed_at: datetime
    passed: bool
    certificate_code: str | None


def _day_bounds(start_date: date | None, end_date: date | None) -> tuple[datetime | None, datetime | None]:
    start = datetime.combine(start_date, time.min, tzinfo=timezone.utc) if start_date else None
    end = datetime.combine(end_date, time.min, tzinfo=timezone.utc) + timedelta(days=1) if end_date else None
    return start, end


def list_completions(
    db: Session,
    course_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    passed: bool | None = None,
) -> list[CompletionRow]:
    # Credit only shown for a passed attempt - a failed one earned none. The
    # snapshot wins once it exists (feature 024); before a passed attempt is
    # claimed it falls back to the course's current award, same as
    # certificates.py's own pre-claim fallback.
    credit_award = case(
        (Attempt.passed.is_(True), func.coalesce(Attempt.cert_credit_award, Course.credit_award)),
        else_=None,
    )
    participant_name = func.coalesce(User.display_name, Attempt.recipient_name)

    stmt = (
        select(
            Attempt.public_id,
            Course.title.label("course_title"),
            participant_name.label("participant_name"),
            User.email.label("participant_email"),
            credit_award.label("credit_award"),
            Attempt.completed_at,
            Attempt.passed,
            Attempt.certificate_code,
        )
        .select_from(Attempt)
        .join(Course, Course.id == Attempt.course_id)
        .outerjoin(User, User.id == Attempt.user_id)
        .where(Attempt.completed_at.is_not(None))
        .order_by(Attempt.completed_at.desc())
    )
    if course_id is not None:
        stmt = stmt.where(Attempt.course_id == course_id)
    start, end = _day_bounds(start_date, end_date)
    if start is not None:
        stmt = stmt.where(Attempt.completed_at >= start)
    if end is not None:
        stmt = stmt.where(Attempt.completed_at < end)
    if passed is not None:
        stmt = stmt.where(Attempt.passed.is_(passed))

    rows = db.execute(stmt).all()
    return [
        CompletionRow(
            attempt_id=row.public_id,
            course_title=row.course_title,
            participant_name=row.participant_name,
            participant_email=row.participant_email,
            credit_award=row.credit_award,
            completed_at=row.completed_at,
            passed=row.passed,
            certificate_code=row.certificate_code,
        )
        for row in rows
    ]


def stream_csv(rows: list[CompletionRow]) -> Iterator[str]:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_HEADER)
    yield buffer.getvalue()

    for row in rows:
        buffer.seek(0)
        buffer.truncate(0)
        writer.writerow(
            [
                str(row.attempt_id),
                row.course_title,
                row.participant_name or "",
                row.participant_email or "",
                row.credit_award if row.credit_award is not None else "",
                row.completed_at.isoformat(),
                row.passed,
                row.certificate_code or "",
            ]
        )
        yield buffer.getvalue()
