from pydantic import BaseModel, Field


class HeartbeatRequest(BaseModel):
    position: int = Field(ge=0)


class WatchProgressResponse(BaseModel):
    watched_seconds: int
    required_seconds: int | None
    duration_seconds: int | None
    ratio: float
    unlocked: bool
