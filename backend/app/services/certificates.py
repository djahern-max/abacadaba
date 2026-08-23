import io
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.constants.delivery_methods import DELIVERY_METHOD_SELF_STUDY
from app.models.attempt import Attempt
from app.models.question import QUESTION_KIND_ASSESSMENT
from app.services import courses as courses_service
from app.services import sponsor_profile as sponsor_profile_service

# Feature 008 is done: an attempt with a signed in user gets its certificate
# name from the account automatically; anonymous attempts still type one in.

# 9.01 item 10: "NASBA time statement stating that CPE credits have been
# granted on a 50-minute hour." Fixed text, not attempt data - identical on
# every certificate abacadaba has ever issued or ever will, so it needs no
# snapshot column.
NASBA_TIME_STATEMENT = "CPE credit has been granted based on a 50-minute hour, per NASBA Standards."

CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no O, 0, I, 1, L
_CODE_LENGTH = 12
_GROUP_SIZE = 4

PAGE_SIZE = landscape(LETTER)


class AttemptNotFoundError(Exception):
    """Raised when a public_id does not match any attempt."""


class AttemptNotEligibleError(Exception):
    """Raised when an attempt has not completed and passed."""


class CertificateNotClaimedError(Exception):
    """Raised when a PDF is requested before a certificate has been claimed."""


class RecipientNameRequiredError(Exception):
    """Raised when an anonymous attempt's certificate is claimed without a name."""


@dataclass
class CertificateData:
    certificate_code: str
    recipient_name: str
    course_slug: str
    course_title: str
    score: int
    question_count: int
    completed_at: datetime
    is_account_holder: bool
    field_of_study: str
    delivery_method: str
    credit_award: Decimal | None
    sponsor_name: str
    sponsor_registry_id: str
    sponsor_state_registry_ids: str | None
    issued_at: datetime | None


def generate_code(db: Session) -> str:
    while True:
        raw = "".join(secrets.choice(CODE_ALPHABET) for _ in range(_CODE_LENGTH))
        code = "-".join(raw[i : i + _GROUP_SIZE] for i in range(0, _CODE_LENGTH, _GROUP_SIZE))
        taken = db.execute(select(Attempt.id).where(Attempt.certificate_code == code)).scalar_one_or_none()
        if taken is None:
            return code


def _normalize_code(raw: str) -> str:
    cleaned = raw.strip().upper().replace("-", "")
    groups = [cleaned[i : i + _GROUP_SIZE] for i in range(0, len(cleaned), _GROUP_SIZE)]
    return "-".join(groups)


def _to_data(db: Session, attempt: Attempt) -> CertificateData:
    # course_slug is routing metadata for the download filename, never
    # asserted certificate content (it isn't on the PDF or the verify page),
    # so it's the one field that's fine to keep reading live off the course
    # even for a snapshot-backed attempt.
    course_slug = attempt.course.slug

    if attempt.cert_course_title is not None:
        return CertificateData(
            certificate_code=attempt.certificate_code,
            recipient_name=attempt.recipient_name,
            course_slug=course_slug,
            course_title=attempt.cert_course_title,
            score=attempt.score,
            question_count=attempt.cert_question_count,
            completed_at=attempt.completed_at,
            is_account_holder=attempt.user_id is not None,
            field_of_study=attempt.cert_field_of_study,
            delivery_method=attempt.cert_delivery_method,
            credit_award=attempt.cert_credit_award,
            sponsor_name=attempt.cert_sponsor_name,
            sponsor_registry_id=attempt.cert_sponsor_registry_id,
            sponsor_state_registry_ids=attempt.cert_sponsor_state_registry_ids,
            issued_at=attempt.cert_issued_at,
        )

    # Pre-024 certificate: claimed before this feature shipped, so it has
    # no snapshot - the columns above are nullable for exactly this case.
    # Backfilling them would mean fabricating a snapshot from data that was
    # never actually frozen (the sponsor concept didn't exist yet, and the
    # course may have changed since); reading live, as these always have,
    # is the more honest of the two options current-feature.md offered.
    sponsor = sponsor_profile_service.get_sponsor_profile(db)
    return CertificateData(
        certificate_code=attempt.certificate_code,
        recipient_name=attempt.recipient_name,
        course_slug=course_slug,
        course_title=attempt.course.title,
        score=attempt.score,
        question_count=courses_service.published_question_count(
            db, attempt.course_id, kind=QUESTION_KIND_ASSESSMENT
        ),
        completed_at=attempt.completed_at,
        is_account_holder=attempt.user_id is not None,
        field_of_study=attempt.course.field_of_study,
        delivery_method=DELIVERY_METHOD_SELF_STUDY,
        credit_award=attempt.course.credit_award,
        sponsor_name=sponsor.name,
        sponsor_registry_id=sponsor.national_registry_id,
        sponsor_state_registry_ids=sponsor.state_registry_ids,
        issued_at=None,
    )


def claim_certificate(db: Session, public_id: uuid.UUID, recipient_name: str | None) -> CertificateData:
    stmt = (
        select(Attempt)
        .where(Attempt.public_id == public_id)
        .options(selectinload(Attempt.course), selectinload(Attempt.user))
    )
    attempt = db.execute(stmt).scalar_one_or_none()
    if attempt is None:
        raise AttemptNotFoundError(f"Attempt {public_id} not found")
    if attempt.completed_at is None or not attempt.passed:
        raise AttemptNotEligibleError("This attempt has not passed yet")

    if attempt.user is not None:
        name = attempt.user.display_name
    elif recipient_name:
        name = recipient_name
    else:
        raise RecipientNameRequiredError("recipient_name is required for an anonymous attempt")

    attempt.recipient_name = name
    if attempt.certificate_code is None:
        # First claim only - a second claim (feature 007) keeps this code
        # and, from here on, keeps the snapshot below too. Written in the
        # same transaction as the code itself: a certificate_code with no
        # snapshot is a state _to_data can't render.
        attempt.certificate_code = generate_code(db)
        sponsor = sponsor_profile_service.get_sponsor_profile(db)
        attempt.cert_course_title = attempt.course.title
        attempt.cert_field_of_study = attempt.course.field_of_study
        attempt.cert_delivery_method = DELIVERY_METHOD_SELF_STUDY
        attempt.cert_credit_award = attempt.course.credit_award
        attempt.cert_question_count = courses_service.published_question_count(
            db, attempt.course_id, kind=QUESTION_KIND_ASSESSMENT
        )
        attempt.cert_sponsor_name = sponsor.name
        attempt.cert_sponsor_registry_id = sponsor.national_registry_id
        attempt.cert_sponsor_state_registry_ids = sponsor.state_registry_ids
        attempt.cert_issued_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(attempt)

    return _to_data(db, attempt)


def get_certificate_for_download(db: Session, public_id: uuid.UUID) -> CertificateData:
    stmt = select(Attempt).where(Attempt.public_id == public_id).options(selectinload(Attempt.course))
    attempt = db.execute(stmt).scalar_one_or_none()
    if attempt is None:
        raise AttemptNotFoundError(f"Attempt {public_id} not found")
    if attempt.completed_at is None or not attempt.passed or attempt.certificate_code is None:
        raise CertificateNotClaimedError("This attempt has no claimed certificate")

    return _to_data(db, attempt)


def verify_code(db: Session, code: str) -> CertificateData | None:
    normalized = _normalize_code(code)
    stmt = select(Attempt).where(Attempt.certificate_code == normalized).options(selectinload(Attempt.course))
    attempt = db.execute(stmt).scalar_one_or_none()
    if attempt is None:
        return None
    return _to_data(db, attempt)


def _fit_font_size(pdf: canvas.Canvas, text: str, font_name: str, max_width: float, start_size: float, min_size: float = 10) -> float:
    size = start_size
    while size > min_size and pdf.stringWidth(text, font_name, size) > max_width:
        size -= 1
    return size


def _draw_field(pdf: canvas.Canvas, x: float, y: float, column_width: float, label: str, value: str) -> None:
    pdf.setFont("Helvetica-Bold", 8)
    pdf.setFillGray(0.35)
    pdf.drawString(x, y, label.upper())

    value_size = _fit_font_size(pdf, value, "Helvetica", column_width, 10, min_size=6)
    pdf.setFont("Helvetica", value_size)
    pdf.setFillGray(0.1)
    pdf.drawString(x, y - 13, value)


def render_pdf(info: CertificateData) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=PAGE_SIZE)
    width, height = PAGE_SIZE
    margin = 60
    max_text_width = width - 2 * margin

    pdf.setFont("Helvetica", 14)
    pdf.setFillGray(0.4)
    pdf.drawCentredString(width / 2, height - 90, "abacadaba")

    pdf.setFont("Helvetica-Bold", 26)
    pdf.setFillGray(0.1)
    pdf.drawCentredString(width / 2, height - 150, "Certificate of Completion")

    name_size = _fit_font_size(pdf, info.recipient_name, "Helvetica-Bold", max_text_width, 40)
    pdf.setFont("Helvetica-Bold", name_size)
    pdf.drawCentredString(width / 2, height - 230, info.recipient_name)

    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(width / 2, height - 270, "has completed")

    title_size = _fit_font_size(pdf, info.course_title, "Helvetica-Bold", max_text_width, 22)
    pdf.setFont("Helvetica-Bold", title_size)
    pdf.drawCentredString(width / 2, height - 305, info.course_title)

    score_text = f"Scored {info.score} out of {info.question_count}"
    date_text = info.completed_at.strftime("%B %d, %Y")
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, height - 345, f"{score_text}  —  {date_text}")

    # Section 9.01's required documentation fields not already covered by
    # the centred lines above (participant name, course title, date of
    # completion), laid out as a labelled block rather than more centred
    # lines - current-feature.md's own instruction, since this is now a
    # fairly full page rather than a sparse one. Two columns of three rows.
    credit_text = f"{info.credit_award} CPE credit(s)" if info.credit_award is not None else "—"
    state_registry_text = info.sponsor_state_registry_ids or "None"
    fields = [
        ("Field of Study", info.field_of_study),
        ("Type of Formal Learning Program", info.delivery_method),
        ("CPE Credit Awarded", credit_text),
        ("Sponsor", info.sponsor_name),
        ("NASBA Sponsor Registry ID", info.sponsor_registry_id),
        ("State Registry ID(s)", state_registry_text),
    ]
    col_gap = 24
    column_width = (max_text_width - col_gap) / 2
    row_height = 34
    block_top = height - 385
    for index, (label, value) in enumerate(fields):
        row, col = divmod(index, 2)
        x = margin + col * (column_width + col_gap)
        y = block_top - row * row_height
        _draw_field(pdf, x, y, column_width, label, value)

    statement_y = block_top - 3 * row_height - 6
    pdf.setFont("Helvetica-Oblique", 8)
    pdf.setFillGray(0.4)
    pdf.drawCentredString(width / 2, statement_y, NASBA_TIME_STATEMENT)

    verify_url = f"{settings.site_url}/verify/{info.certificate_code}"
    pdf.setFont("Helvetica", 9)
    pdf.setFillGray(0.5)
    pdf.drawCentredString(width / 2, margin, f"Verification code: {info.certificate_code}    {verify_url}")

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
