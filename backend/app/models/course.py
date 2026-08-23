from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants.fields_of_study import DEFAULT_FIELD_OF_STUDY
from app.constants.program_levels import PROGRAM_LEVELS
from app.db import Base

DEFAULT_REVIEW_CYCLE = "biennial"


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    thumbnail_key: Mapped[str | None] = mapped_column(String, nullable=True)
    retake_cooldown_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    max_attempts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    program_level: Mapped[str] = mapped_column(
        String, nullable=False, default=PROGRAM_LEVELS[0], server_default=PROGRAM_LEVELS[0]
    )
    field_of_study: Mapped[str] = mapped_column(
        String, nullable=False, default=DEFAULT_FIELD_OF_STUDY, server_default=DEFAULT_FIELD_OF_STUDY
    )
    prerequisites: Mapped[str | None] = mapped_column(Text, nullable=True)
    advance_preparation: Mapped[str | None] = mapped_column(Text, nullable=True)
    developer_id: Mapped[int | None] = mapped_column(
        ForeignKey("subject_matter_experts.id"), nullable=True, index=True
    )
    reviewer_id: Mapped[int | None] = mapped_column(
        ForeignKey("subject_matter_experts.id"), nullable=True, index=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Bumped by every mutation a participant would see - see
    # app/services/admin_content.py's touch_content_updated_at, the single
    # choke point for that rule. Never bumped by review-chain fields.
    content_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    review_cycle: Mapped[str] = mapped_column(
        String, nullable=False, default=DEFAULT_REVIEW_CYCLE, server_default=DEFAULT_REVIEW_CYCLE
    )
    # Feature 022: the word-count credit formula (7.02.6/7.02.7). Stored
    # inputs plus the computed result, not just the answer - see
    # current-feature.md, "Store the inputs, not just the answer". Nullable
    # because a course starts with no credit computed at all; staleness is
    # derived (never a stored bool) exactly like the review chain's, from
    # `credit_computed_at is None or credit_computed_at < content_updated_at`.
    credit_award: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    credit_raw_minutes: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    credit_word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    credit_av_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    credit_question_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    credit_formula_version: Mapped[str | None] = mapped_column(String, nullable=True)
    credit_computed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Feature 023: the qualified assessment's minimum passing grade (6.01.2
    # sets 70 percent as a floor, not a default a sponsor may relax - the
    # CHECK constraint is the enforcement, not just this default).
    pass_ratio: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, default=Decimal("0.70"), server_default="0.70"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="course",
        order_by="Lesson.position",
        cascade="all, delete-orphan",
    )
    learning_objectives: Mapped[list["LearningObjective"]] = relationship(
        back_populates="course",
        order_by="LearningObjective.position",
        cascade="all, delete-orphan",
    )
    sources: Mapped[list["Source"]] = relationship(
        back_populates="course",
        order_by="Source.position",
        cascade="all, delete-orphan",
    )
    developer: Mapped["SubjectMatterExpert | None"] = relationship(foreign_keys=[developer_id])
    reviewer: Mapped["SubjectMatterExpert | None"] = relationship(foreign_keys=[reviewer_id])

    @property
    def has_thumbnail(self) -> bool:
        return self.thumbnail_key is not None
