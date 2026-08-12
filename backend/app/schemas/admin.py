from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AdminChoiceIn(BaseModel):
    text: str
    is_correct: bool = False


class AdminChoiceUpdate(BaseModel):
    text: str | None = None
    is_correct: bool | None = None


class AdminChoice(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    is_correct: bool
    position: int


class AdminQuestionIn(BaseModel):
    prompt: str


class AdminQuestionUpdate(BaseModel):
    prompt: str | None = None


class AdminQuestion(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt: str
    position: int
    choices: list[AdminChoice]


class AdminLessonCreate(BaseModel):
    title: str
    slug: str | None = None
    description: str = ""
    duration_seconds: int | None = None


class AdminLessonUpdate(BaseModel):
    """Partial update. Changing `slug` on a published lesson breaks any
    links already handed out, so the caller must set it explicitly rather
    than have it inferred from a title change."""

    title: str | None = None
    slug: str | None = None
    description: str | None = None
    duration_seconds: int | None = None
    required_watch_ratio: float | None = Field(default=None, ge=0, le=1)


class AdminLesson(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    course_slug: str
    position: int
    slug: str
    title: str
    description: str
    duration_seconds: int | None
    video_key: str | None
    thumbnail_key: str | None
    required_watch_ratio: float
    is_published: bool
    questions: list[AdminQuestion]


class AdminCourseCreate(BaseModel):
    title: str
    slug: str | None = None
    description: str = ""


class AdminCourseUpdate(BaseModel):
    """Partial update. Changing `slug` on a published course breaks any
    links already handed out, so the caller must set it explicitly rather
    than have it inferred from a title change."""

    title: str | None = None
    slug: str | None = None
    description: str | None = None
    retake_cooldown_minutes: int | None = Field(default=None, ge=0)
    max_attempts: int | None = Field(default=None, ge=1)


class AdminCourseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    is_published: bool
    lesson_count: int


class AdminCourse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    description: str
    thumbnail_key: str | None
    retake_cooldown_minutes: int
    max_attempts: int | None
    is_published: bool
    lessons: list[AdminLesson]


class MoveRequest(BaseModel):
    direction: Literal["up", "down"]


class SetCorrectChoiceRequest(BaseModel):
    choice_id: int
