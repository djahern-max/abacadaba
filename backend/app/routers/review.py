import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user, get_viewer_id
from app.models.user import User
from app.schemas.review import ReviewAnswerRequest, ReviewAnswerResponse, ReviewQuestionsPublic
from app.services import review as review_service

router = APIRouter()


@router.get(
    "/courses/{slug}/lessons/{lesson_slug}/review",
    response_model=ReviewQuestionsPublic,
)
def get_review_questions(slug: str, lesson_slug: str, db: Session = Depends(get_db)):
    questions = review_service.get_review_questions(db, slug, lesson_slug)
    if questions is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return ReviewQuestionsPublic(questions=questions)


@router.post(
    "/courses/{slug}/lessons/{lesson_slug}/review/{question_id}",
    response_model=ReviewAnswerResponse,
)
def answer_review_question(
    slug: str,
    lesson_slug: str,
    question_id: int,
    payload: ReviewAnswerRequest,
    db: Session = Depends(get_db),
    viewer_id: uuid.UUID = Depends(get_viewer_id),
    user: User | None = Depends(get_current_user),
):
    try:
        result = review_service.record_answer(
            db, slug, lesson_slug, question_id, payload.choice_id, viewer_id, user.id if user else None
        )
    except review_service.QuestionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Question not found for this lesson") from exc
    except review_service.InvalidChoiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ReviewAnswerResponse(correct=result.correct, feedback=result.feedback)
