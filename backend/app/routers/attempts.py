import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user, get_viewer_id, require_user
from app.models.user import User
from app.schemas.attempt import (
    AttemptAnswerRequest,
    AttemptAnswerResponse,
    AttemptResult,
    AttemptStart,
    UserAttempt,
)
from app.services import attempts as attempts_service

router = APIRouter()


@router.post("/lessons/{slug}/attempts", response_model=AttemptStart, status_code=201)
def start_attempt(
    slug: str,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
    viewer_id: uuid.UUID = Depends(get_viewer_id),
):
    try:
        result = attempts_service.start_attempt(db, slug, user, viewer_id)
    except attempts_service.WatchRequirementNotMetError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except attempts_service.MaxAttemptsExceededError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except attempts_service.RetakeCooldownError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="This lesson has no quiz yet")

    return AttemptStart(
        attempt_id=result.attempt_id, lesson_slug=result.lesson_slug, question_count=result.question_count
    )


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
        correct=result.correct,
        correct_choice_id=result.correct_choice_id,
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
        lesson_slug=result.lesson_slug,
        lesson_title=result.lesson_title,
        score=result.score,
        question_count=result.question_count,
        passed=result.passed,
        completed_at=result.completed_at,
        certificate_code=result.certificate_code,
    )


@router.get("/me/attempts", response_model=list[UserAttempt])
def get_my_attempts(db: Session = Depends(get_db), user: User = Depends(require_user)):
    results = attempts_service.list_user_attempts(db, user)
    return [
        UserAttempt(
            attempt_id=r.attempt_id,
            lesson_title=r.lesson_title,
            lesson_slug=r.lesson_slug,
            score=r.score,
            passed=r.passed,
            completed_at=r.completed_at,
            certificate_code=r.certificate_code,
        )
        for r in results
    ]
