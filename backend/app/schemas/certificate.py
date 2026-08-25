from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class CertificateClaim(BaseModel):
    recipient_name: str | None = None

    @field_validator("recipient_name")
    @classmethod
    def strip_and_check_length(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not (2 <= len(stripped) <= 80):
            raise ValueError("recipient_name must be 2 to 80 characters after stripping whitespace")
        return stripped


class CertificateInfo(BaseModel):
    """A CPE-presented course's certificate response - unchanged by feature
    029, plus the program_kind flag itself. See CertificateInfoGeneral below
    for the general-course shape: distinct fields, not a subclass, because a
    general certificate doesn't just omit fields, it renames sponsor_name to
    issued_by - the guard test checks for the substring "sponsor" anywhere
    in the payload, key or value, so the key itself must not exist."""

    model_config = ConfigDict(from_attributes=True)

    certificate_code: str
    recipient_name: str
    course_title: str
    score: int
    question_count: int
    completed_at: datetime
    program_kind: str
    field_of_study: str
    delivery_method: str
    credit_award: Decimal | None
    sponsor_name: str
    sponsor_registry_id: str | None
    sponsor_state_registry_ids: str | None
    registry_status: str
    issued_at: datetime | None


class CertificateInfoGeneral(BaseModel):
    """A general course's certificate response. See current-feature.md,
    Part 4: keeps only the participant name, course title, completion date,
    score, issuing organization, and verification code."""

    model_config = ConfigDict(from_attributes=True)

    certificate_code: str
    recipient_name: str
    course_title: str
    score: int
    question_count: int
    completed_at: datetime
    program_kind: str
    issued_by: str
    issued_at: datetime | None


class CertificateVerification(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    valid: bool
    certificate_code: str | None = None
    recipient_name: str | None = None
    course_title: str | None = None
    score: int | None = None
    question_count: int | None = None
    completed_at: datetime | None = None
    is_account_holder: bool | None = None
    program_kind: str | None = None
    field_of_study: str | None = None
    delivery_method: str | None = None
    credit_award: Decimal | None = None
    sponsor_name: str | None = None
    sponsor_registry_id: str | None = None
    sponsor_state_registry_ids: str | None = None
    registry_status: str | None = None
    issued_at: datetime | None = None


class CertificateVerificationGeneral(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    valid: bool
    certificate_code: str | None = None
    recipient_name: str | None = None
    course_title: str | None = None
    score: int | None = None
    question_count: int | None = None
    completed_at: datetime | None = None
    is_account_holder: bool | None = None
    program_kind: str | None = None
    issued_by: str | None = None
    issued_at: datetime | None = None
