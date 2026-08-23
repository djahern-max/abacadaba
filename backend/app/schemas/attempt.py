from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AttemptStart(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attempt_id: UUID
    course_slug: str
    question_count: int


class AttemptAnswerRequest(BaseModel):
    question_id: int
    choice_id: int


class AttemptAnswerResponse(BaseModel):
    # No correctness here, deliberately - see app/services/attempts.py's
    # AnswerResult. The application cannot know mid-attempt whether the
    # participant will pass, and 6.01.2 (no test bank) forbids feedback on a
    # failed assessment.
    answered_count: int
    question_count: int


class AnsweredQuestion(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    question_id: int
    prompt: str
    chosen_choice_id: int
    chosen_choice_text: str
    correct_choice_id: int
    correct_choice_text: str
    is_correct: bool
    # Only ever present here because this whole list is only ever present on
    # a passed attempt (6.01.2 sub-ii b) - see AttemptResult.answers.
    feedback: str | None = None


class AttemptResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attempt_id: UUID
    course_slug: str
    course_title: str
    score: int
    question_count: int
    passed: bool
    completed_at: datetime
    certificate_code: str | None = None
    # Populated only when passed - see AttemptResultData.answers.
    answers: list[AnsweredQuestion] | None = None


class UserAttempt(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attempt_id: UUID
    course_title: str
    course_slug: str
    score: int
    passed: bool
    completed_at: datetime
    certificate_code: str | None = None
