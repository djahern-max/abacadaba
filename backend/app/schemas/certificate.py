from datetime import datetime

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
    model_config = ConfigDict(from_attributes=True)

    certificate_code: str
    recipient_name: str
    course_title: str
    score: int
    question_count: int
    completed_at: datetime


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
