import io
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.certificate import CertificateClaim, CertificateInfo, CertificateVerification
from app.services import certificates as certificates_service

router = APIRouter()


def _to_info(data: certificates_service.CertificateData) -> CertificateInfo:
    return CertificateInfo(
        certificate_code=data.certificate_code,
        recipient_name=data.recipient_name,
        lesson_title=data.lesson_title,
        score=data.score,
        question_count=data.question_count,
        completed_at=data.completed_at,
    )


@router.post("/attempts/{attempt_id}/certificate", response_model=CertificateInfo)
def claim_certificate(attempt_id: uuid.UUID, claim: CertificateClaim, db: Session = Depends(get_db)):
    try:
        data = certificates_service.claim_certificate(db, attempt_id, claim.recipient_name)
    except certificates_service.AttemptNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Attempt not found") from exc
    except certificates_service.AttemptNotEligibleError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except certificates_service.RecipientNameRequiredError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return _to_info(data)


@router.get("/attempts/{attempt_id}/certificate.pdf")
def download_certificate(attempt_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        data = certificates_service.get_certificate_for_download(db, attempt_id)
    except certificates_service.AttemptNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Attempt not found") from exc
    except certificates_service.CertificateNotClaimedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    pdf_bytes = certificates_service.render_pdf(data)
    filename = f"abacadaba-{data.lesson_slug}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/certificates/{code}", response_model=CertificateVerification)
def verify_certificate(code: str, db: Session = Depends(get_db)):
    data = certificates_service.verify_code(db, code)
    if data is None:
        return CertificateVerification(valid=False)

    return CertificateVerification(
        valid=True,
        certificate_code=data.certificate_code,
        recipient_name=data.recipient_name,
        lesson_title=data.lesson_title,
        score=data.score,
        question_count=data.question_count,
        completed_at=data.completed_at,
        is_account_holder=data.is_account_holder,
    )
