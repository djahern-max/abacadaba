from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PolicyUpdate(BaseModel):
    title: str | None = None
    body: str | None = None


class PolicyPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str
    body: str
    updated_at: datetime
    # Whether this policy still carries the seeded placeholder text - not
    # sensitive, so it's exposed on the public route too rather than adding
    # a second admin-only listing endpoint just to read it.
    is_placeholder: bool
