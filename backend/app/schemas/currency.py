from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ReviewCurrencyRowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_id: int
    title: str
    is_published: bool
    reviewed_at: datetime
    review_cycle: str
    due_at: datetime
    days_overdue: int


class PublishedButEditedRowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_id: int
    title: str
    reviewed_at: datetime
    content_updated_at: datetime
    days_since_edit: int


class ExpirationRowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_id: int
    title: str
    is_published: bool
    expires_on: date
    days_until_expiry: int


class CurrencyDashboardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    overdue_review: list[ReviewCurrencyRowOut]
    due_soon: list[ReviewCurrencyRowOut]
    published_but_edited: list[PublishedButEditedRowOut]
    expired_or_expiring: list[ExpirationRowOut]
