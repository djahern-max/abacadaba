from pydantic import BaseModel, Field


class HeartbeatRequest(BaseModel):
    position: int = Field(ge=0)


class WatchProgressResponse(BaseModel):
    watched_seconds: int
    required_seconds: int | None
    duration_seconds: int | None
    ratio: float
    unlocked: bool


class LessonWatchStatusResponse(BaseModel):
    lesson_slug: str
    lesson_title: str
    position: int
    progress: WatchProgressResponse


class CourseWatchStatusResponse(BaseModel):
    gate_met: bool
    lessons: list[LessonWatchStatusResponse]
