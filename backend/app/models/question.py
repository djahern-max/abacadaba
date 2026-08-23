from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

# Feature 023: review questions reinforce learning and give feedback
# (5.01.2.1/5.01.2.2); assessment questions gate credit (6.01.2). The two
# must never be scored together - see app/services/quiz.py and
# app/services/attempts.py, which filter to QUESTION_KIND_ASSESSMENT only.
QUESTION_KIND_REVIEW = "review"
QUESTION_KIND_ASSESSMENT = "assessment"
QUESTION_KINDS = (QUESTION_KIND_REVIEW, QUESTION_KIND_ASSESSMENT)
DEFAULT_QUESTION_KIND = QUESTION_KIND_ASSESSMENT


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (UniqueConstraint("lesson_id", "position"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(
        String, nullable=False, default=DEFAULT_QUESTION_KIND, server_default=DEFAULT_QUESTION_KIND
    )
    # Shown after a review question is answered (5.01.2.2). On an assessment
    # question, withheld during the attempt and on a failed result; shown on
    # the result screen only after a pass (6.01.2 sub-ii b, no test bank) -
    # see app/services/attempts.py::get_result.
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    # The course-level learning objective this question tests (feature 023a).
    # Nullable: review questions are never required to be tagged, and an
    # assessment question mid-authoring has none yet. SET NULL, not CASCADE -
    # deleting an objective must not delete the questions that tested it; it
    # untags them, and publish validation reports the resulting coverage gap.
    objective_id: Mapped[int | None] = mapped_column(
        ForeignKey("learning_objectives.id", ondelete="SET NULL"), nullable=True, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    lesson: Mapped["Lesson"] = relationship(back_populates="questions")
    choices: Mapped[list["Choice"]] = relationship(
        back_populates="question",
        order_by="Choice.position",
        cascade="all, delete-orphan",
    )
