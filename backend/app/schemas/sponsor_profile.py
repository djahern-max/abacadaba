from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AdminSponsorProfileUpdate(BaseModel):
    name: str | None = None
    national_registry_id: str | None = None
    state_registry_ids: str | None = None
    website: str | None = None
    contact_email: str | None = None
    address: str | None = None
    registry_status: str | None = None


class AdminSponsorProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    national_registry_id: str
    state_registry_ids: str | None
    website: str
    contact_email: str
    address: str
    registry_status: str
    updated_at: datetime
    # So the admin page can tell a participant-visible course is blocked on
    # this record without duplicating validate_for_publish's own rule.
    missing_fields: list[str]
