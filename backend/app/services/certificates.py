import io
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime

from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.pdfgen import canvas
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.models.attempt import Attempt
from app.models.question import Question

# Feature 008 is done: an attempt with a signed in user gets its certificate
# name from the account automatically; anonymous attempts still type one in.

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
    lesson_slug: str
    lesson_title: str
    score: int
    question_count: int
    completed_at: datetime
    is_account_holder: bool


def _question_count(db: Session, lesson_id: int) -> int:
    stmt = select(func.count()).select_from(Question).where(Question.lesson_id == lesson_id)
    return db.execute(stmt).scalar_one()


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
    return CertificateData(
        certificate_code=attempt.certificate_code,
        recipient_name=attempt.recipient_name,
        lesson_slug=attempt.lesson.slug,
        lesson_title=attempt.lesson.title,
        score=attempt.score,
        question_count=_question_count(db, attempt.lesson_id),
        completed_at=attempt.completed_at,
        is_account_holder=attempt.user_id is not None,
    )


def claim_certificate(db: Session, public_id: uuid.UUID, recipient_name: str | None) -> CertificateData:
    stmt = (
        select(Attempt)
        .where(Attempt.public_id == public_id)
        .options(selectinload(Attempt.lesson), selectinload(Attempt.user))
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
        attempt.certificate_code = generate_code(db)
    db.commit()
    db.refresh(attempt)

    return _to_data(db, attempt)


def get_certificate_for_download(db: Session, public_id: uuid.UUID) -> CertificateData:
    stmt = select(Attempt).where(Attempt.public_id == public_id).options(selectinload(Attempt.lesson))
    attempt = db.execute(stmt).scalar_one_or_none()
    if attempt is None:
        raise AttemptNotFoundError(f"Attempt {public_id} not found")
    if attempt.completed_at is None or not attempt.passed or attempt.certificate_code is None:
        raise CertificateNotClaimedError("This attempt has no claimed certificate")

    return _to_data(db, attempt)


def verify_code(db: Session, code: str) -> CertificateData | None:
    normalized = _normalize_code(code)
    stmt = select(Attempt).where(Attempt.certificate_code == normalized).options(selectinload(Attempt.lesson))
    attempt = db.execute(stmt).scalar_one_or_none()
    if attempt is None:
        return None
    return _to_data(db, attempt)


def _fit_font_size(pdf: canvas.Canvas, text: str, font_name: str, max_width: float, start_size: float, min_size: float = 10) -> float:
    size = start_size
    while size > min_size and pdf.stringWidth(text, font_name, size) > max_width:
        size -= 1
    return size


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

    title_size = _fit_font_size(pdf, info.lesson_title, "Helvetica-Bold", max_text_width, 22)
    pdf.setFont("Helvetica-Bold", title_size)
    pdf.drawCentredString(width / 2, height - 305, info.lesson_title)

    score_text = f"Scored {info.score} out of {info.question_count}"
    date_text = info.completed_at.strftime("%B %d, %Y")
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, height - 345, f"{score_text}  —  {date_text}")

    verify_url = f"{settings.site_url}/verify/{info.certificate_code}"
    pdf.setFont("Helvetica", 9)
    pdf.setFillGray(0.5)
    pdf.drawCentredString(width / 2, margin, f"Verification code: {info.certificate_code}    {verify_url}")

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
