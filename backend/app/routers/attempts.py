import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_user
from app.models.user import User
from app.schemas.attempt import (
    AnsweredQuestion,
    AttemptAnswerRequest,
    AttemptAnswerResponse,
    AttemptResult,
    UserAttempt,
)
from app.services import attempts as attempts_service

router = APIRouter()


@router.post("/attempts/{attempt_id}/answers", response_model=AttemptAnswerResponse)
def answer_attempt(attempt_id: uuid.UUID, answer: AttemptAnswerRequest, db: Session = Depends(get_db)):
    try:
        result = attempts_service.record_answer(db, attempt_id, answer.question_id, answer.choice_id)
    except attempts_service.AttemptNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Attempt not found") from exc
    except attempts_service.QuestionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Question not found for this attempt") from exc
    except attempts_service.AttemptCompleteError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except attempts_service.DuplicateAnswerError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except attempts_service.InvalidChoiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return AttemptAnswerResponse(
        answered_count=result.answered_count,
        question_count=result.question_count,
    )


@router.get("/attempts/{attempt_id}/result", response_model=AttemptResult)
def get_attempt_result(attempt_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        result = attempts_service.get_result(db, attempt_id)
    except attempts_service.AttemptNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Attempt not found") from exc
    except attempts_service.AttemptNotCompleteError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return AttemptResult(
        attempt_id=result.attempt_id,
        course_slug=result.course_slug,
        course_title=result.course_title,
        score=result.score,
        question_count=result.question_count,
        passed=result.passed,
        completed_at=result.completed_at,
        certificate_code=result.certificate_code,
        answers=[AnsweredQuestion.model_validate(answer) for answer in result.answers]
        if result.answers is not None
        else None,
    )


@router.get("/me/attempts", response_model=list[UserAttempt])
def get_my_attempts(db: Session = Depends(get_db), user: User = Depends(require_user)):
    results = attempts_service.list_user_attempts(db, user)
    return [
        UserAttempt(
            attempt_id=r.attempt_id,
            course_title=r.course_title,
            course_slug=r.course_slug,
            score=r.score,
            passed=r.passed,
            completed_at=r.completed_at,
            certificate_code=r.certificate_code,
        )
        for r in results
    ]
