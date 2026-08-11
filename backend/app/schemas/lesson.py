from pydantic import BaseModel, ConfigDict


class LessonSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    description: str
    duration_seconds: int | None
    has_thumbnail: bool


class LessonDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    description: str
    duration_seconds: int | None
    video_key: str | None


class VideoUrlResponse(BaseModel):
    url: str
    expires_in: int


class ThumbnailUrlResponse(BaseModel):
    url: str
    expires_in: int
