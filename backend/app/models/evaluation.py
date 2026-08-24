from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Evaluation(Base):
    """A participant's program evaluation (4.04/4.04.1), one per attempt.

    Columns per dimension, not a rows-per-answer table: the five dimensions
    are a fixed form the Standards define, not a growing entity, and a
    columnar shape aggregates with a single query - see current-feature.md,
    "Columns per dimension, not a rows-per-answer table". Keyed to the
    attempt rather than to course + viewer because the attempt is already
    the completion record and its uniqueness gives one-evaluation-per-
    completion for free.
    """

    __tablename__ = "evaluations"
    __table_args__ = (
        CheckConstraint("objectives_met BETWEEN 1 AND 5", name="ck_evaluations_objectives_met_range"),
        CheckConstraint(
            "prerequisites_appropriate BETWEEN 1 AND 5", name="ck_evaluations_prerequisites_appropriate_range"
        ),
        CheckConstraint("materials_relevant BETWEEN 1 AND 5", name="ck_evaluations_materials_relevant_range"),
        CheckConstraint(
            "time_allotted_appropriate BETWEEN 1 AND 5", name="ck_evaluations_time_allotted_appropriate_range"
        ),
        CheckConstraint("instructor_effective BETWEEN 1 AND 5", name="ck_evaluations_instructor_effective_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("attempts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    objectives_met: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prerequisites_appropriate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    materials_relevant: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_allotted_appropriate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Never written by abacadaba's self study flow - see
    # app/constants/evaluation_dimensions.py. Reserved for superCPE's group
    # programs.
    instructor_effective: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    attempt: Mapped["Attempt"] = relationship()
