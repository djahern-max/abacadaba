import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class AdminCompletionRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attempt_id: uuid.UUID
    course_title: str
    participant_name: str | None
    participant_email: str | None
    credit_award: Decimal | None
    completed_at: datetime
    passed: bool
    certificate_code: str | None
