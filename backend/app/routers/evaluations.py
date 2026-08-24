import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.constants.evaluation_dimensions import dimensions_for_self_study
from app.db import get_db
from app.schemas.evaluation import EvaluationDimensionsResponse, EvaluationIn, EvaluationOut
from app.services import evaluations as evaluations_service

router = APIRouter()


@router.get("/meta/evaluation-dimensions", response_model=EvaluationDimensionsResponse)
def get_evaluation_dimensions():
    return EvaluationDimensionsResponse(dimensions=dimensions_for_self_study())


@router.post("/attempts/{attempt_id}/evaluation", response_model=EvaluationOut)
def submit_evaluation(attempt_id: uuid.UUID, payload: EvaluationIn, db: Session = Depends(get_db)):
    ratings = payload.model_dump(exclude={"comments"})
    try:
        return evaluations_service.submit(db, attempt_id, ratings, payload.comments)
    except evaluations_service.AttemptNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Attempt not found") from exc
    except evaluations_service.AttemptNotCompleteError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except evaluations_service.DuplicateEvaluationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/attempts/{attempt_id}/evaluation", response_model=EvaluationOut | None)
def get_evaluation(attempt_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return evaluations_service.get_for_attempt(db, attempt_id)
    except evaluations_service.AttemptNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Attempt not found") from exc
