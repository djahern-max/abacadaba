import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, index=True, nullable=False, default=uuid.uuid4
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Nullable because attempts created before feature 012 have none. Every new
    # attempt gets one from the viewer_id cookie (feature 011), signed in or not.
    viewer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    shuffle_seed: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recipient_name: Mapped[str | None] = mapped_column(String, nullable=True)
    certificate_code: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    # Feature 024: the certificate snapshot, written once at claim time
    # (see app/services/certificates.py::claim_certificate) from the course
    # and the sponsor profile as they stood that moment, so a later edit to
    # either can never change a certificate already issued. Nullable
    # because an attempt predating this feature - or one never claimed -
    # has none; `_to_data` falls back to reading the live course for those,
    # exactly like `certificate_code` already does under feature 007's
    # first-claim-only rule.
    cert_course_title: Mapped[str | None] = mapped_column(String, nullable=True)
    cert_field_of_study: Mapped[str | None] = mapped_column(String, nullable=True)
    cert_delivery_method: Mapped[str | None] = mapped_column(String, nullable=True)
    cert_credit_award: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    # The assessment question count backing "scored X out of Y" on the PDF -
    # otherwise that line would keep reading courses_service's live count,
    # exactly the drift this feature exists to close.
    cert_question_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cert_sponsor_name: Mapped[str | None] = mapped_column(String, nullable=True)
    cert_sponsor_registry_id: Mapped[str | None] = mapped_column(String, nullable=True)
    cert_sponsor_state_registry_ids: Mapped[str | None] = mapped_column(Text, nullable=True)
    cert_issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    course: Mapped["Course"] = relationship()
    user: Mapped["User | None"] = relationship()
    answers: Mapped[list["AttemptAnswer"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )
