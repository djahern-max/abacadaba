from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SponsorProfile(Base):
    """The CPE program sponsor's own identity record (9.01 items 1, 8, 9).

    Always exactly one row, id 1 - enforced by the CHECK below rather than by
    convention, since a second sponsor row is not a state this application
    has any meaning for. Editable in the admin because this is audit data
    that changes rarely and must be visible to whoever is responsible for
    it; a seed migration inserts the row with empty strings so there is
    always something to edit."""

    __tablename__ = "sponsor_profile"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_sponsor_profile_singleton"),
        CheckConstraint(
            "registry_status IN ('not_registered', 'registered')",
            name="ck_sponsor_profile_registry_status_valid",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, default="", server_default="")
    national_registry_id: Mapped[str] = mapped_column(String, nullable=False, default="", server_default="")
    # Feature 027. Every other field this app can compute, it derives rather
    # than stores (019a's is_placeholder, 022's credit staleness) - this one
    # is a deliberate exception. Whether abacadaba is on the National
    # Registry is a fact about the world, not something inferable from the
    # shape of national_registry_id: a plausible six-digit string is not
    # evidence, and format-sniffing it would produce a confident wrong
    # answer. The sponsor has to state it. Defaults to 'not_registered' so a
    # fresh database, and the pre-existing seeded row, are both honest
    # without anyone doing anything.
    registry_status: Mapped[str] = mapped_column(
        String, nullable=False, default="not_registered", server_default="not_registered"
    )
    # Free form because a sponsor registered with individual state boards
    # carries more than one (9.01 item 9, "if required by the state
    # boards") - not every sponsor has one at all.
    state_registry_ids: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str] = mapped_column(String, nullable=False, default="", server_default="")
    contact_email: Mapped[str] = mapped_column(String, nullable=False, default="", server_default="")
    address: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
