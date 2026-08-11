import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class WatchProgress(Base):
    __tablename__ = "watch_progress"
    __table_args__ = (
        # A signed-in user's progress is unique per lesson regardless of
        # which browser/viewer_id wrote it; an anonymous row is unique per
        # lesson per browser. The two must not overlap, hence partial
        # indexes rather than one constraint - see migration 6f58cd9b86ef.
        Index(
            "ix_watch_progress_lesson_user_unique",
            "lesson_id",
            "user_id",
            unique=True,
            postgresql_where=text("user_id IS NOT NULL"),
        ),
        Index(
            "ix_watch_progress_lesson_viewer_unique",
            "lesson_id",
            "viewer_id",
            unique=True,
            postgresql_where=text("user_id IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    viewer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    watched_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_position: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    lesson: Mapped["Lesson"] = relationship()
