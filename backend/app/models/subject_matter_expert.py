from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SubjectMatterExpert(Base):
    __tablename__ = "subject_matter_experts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    credentials: Mapped[str] = mapped_column(String, nullable=False)
    affiliation: Mapped[str | None] = mapped_column(String, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_licensed_cpa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_tax_attorney: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_enrolled_agent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    license_jurisdiction: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
