from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AdminSMECreate(BaseModel):
    name: str
    credentials: str
    affiliation: str | None = None
    bio: str | None = None
    is_licensed_cpa: bool = False
    is_tax_attorney: bool = False
    is_enrolled_agent: bool = False
    license_jurisdiction: str | None = None


class AdminSMEUpdate(BaseModel):
    name: str | None = None
    credentials: str | None = None
    affiliation: str | None = None
    bio: str | None = None
    is_licensed_cpa: bool | None = None
    is_tax_attorney: bool | None = None
    is_enrolled_agent: bool | None = None
    license_jurisdiction: str | None = None


class AdminSME(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    credentials: str
    affiliation: str | None
    bio: str | None
    is_licensed_cpa: bool
    is_tax_attorney: bool
    is_enrolled_agent: bool
    license_jurisdiction: str | None


class AdminSourceIn(BaseModel):
    citation: str
    url: str | None = None
    retrieved_on: date | None = None


class AdminSourceUpdate(BaseModel):
    citation: str | None = None
    url: str | None = None
    retrieved_on: date | None = None


class AdminSource(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    citation: str
    url: str | None
    retrieved_on: date | None


class AdminObjectiveIn(BaseModel):
    text: str


class AdminObjectiveUpdate(BaseModel):
    text: str | None = None


class AdminObjective(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    position: int


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
    program_level: str | None = None
    field_of_study: str | None = None
    prerequisites: str | None = None
    advance_preparation: str | None = None
    developer_id: int | None = None
    reviewer_id: int | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None
    review_cycle: str | None = None


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
    program_level: str
    field_of_study: str
    prerequisites: str | None
    advance_preparation: str | None
    is_published: bool
    lessons: list[AdminLesson]
    learning_objectives: list[AdminObjective]
    developer_id: int | None
    reviewer_id: int | None
    developer: AdminSME | None
    reviewer: AdminSME | None
    reviewed_at: datetime | None
    review_notes: str | None
    review_cycle: str
    content_updated_at: datetime
    sources: list[AdminSource]


class MoveRequest(BaseModel):
    direction: Literal["up", "down"]


class SetCorrectChoiceRequest(BaseModel):
    choice_id: int
