import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EvaluationDimensionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    question: str


class EvaluationDimensionsResponse(BaseModel):
    dimensions: list[EvaluationDimensionOut]


class EvaluationIn(BaseModel):
    objectives_met: int | None = Field(default=None, ge=1, le=5)
    prerequisites_appropriate: int | None = Field(default=None, ge=1, le=5)
    materials_relevant: int | None = Field(default=None, ge=1, le=5)
    time_allotted_appropriate: int | None = Field(default=None, ge=1, le=5)
    instructor_effective: int | None = Field(default=None, ge=1, le=5)
    comments: str | None = None


class EvaluationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attempt_id: uuid.UUID
    objectives_met: int | None
    prerequisites_appropriate: int | None
    materials_relevant: int | None
    time_allotted_appropriate: int | None
    instructor_effective: int | None
    comments: str | None
    submitted_at: datetime


class DimensionMean(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    mean: float | None


class CourseEvaluationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    response_count: int
    completed_attempts_count: int
    response_rate: float | None
    means: list[DimensionMean]


class EvaluationComment(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    comments: str
    submitted_at: datetime


class CourseEvaluationsResponse(BaseModel):
    summary: CourseEvaluationSummary
    comments: list[EvaluationComment]
