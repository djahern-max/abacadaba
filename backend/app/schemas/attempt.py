from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AttemptStart(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attempt_id: UUID
    lesson_slug: str
    question_count: int


class AttemptAnswerRequest(BaseModel):
    question_id: int
    choice_id: int


class AttemptAnswerResponse(BaseModel):
    correct: bool
    correct_choice_id: int
    answered_count: int
    question_count: int


class AttemptResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attempt_id: UUID
    lesson_slug: str
    lesson_title: str
    score: int
    question_count: int
    passed: bool
    completed_at: datetime
