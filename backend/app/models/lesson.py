from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Lesson(Base):
    __tablename__ = "lessons"
    __table_args__ = (UniqueConstraint("course_id", "position"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    video_key: Mapped[str | None] = mapped_column(String, nullable=True)
    thumbnail_key: Mapped[str | None] = mapped_column(String, nullable=True)
    required_watch_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=0.9, server_default="0.9")
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    course: Mapped["Course"] = relationship(back_populates="lessons")
    questions: Mapped[list["Question"]] = relationship(
        back_populates="lesson",
        order_by="Question.position",
        cascade="all, delete-orphan",
    )

    @property
    def has_thumbnail(self) -> bool:
        return self.thumbnail_key is not None

    @property
    def course_slug(self) -> str:
        return self.course.slug
