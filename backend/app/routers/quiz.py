from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.quiz import AnswerRequest, AnswerResponse, QuizPublic
from app.services import quiz as quiz_service
from app.services import lessons as lessons_service

router = APIRouter()


@router.get("/lessons/{slug}/quiz", response_model=QuizPublic)
def get_quiz(slug: str, db: Session = Depends(get_db)):
    lesson = lessons_service.get_by_slug(db, slug)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    quiz_lesson = quiz_service.get_quiz_for_lesson(db, slug)
    if quiz_lesson is None:
        raise HTTPException(status_code=404, detail="This lesson has no quiz yet")

    return QuizPublic(
        lesson_slug=quiz_lesson.slug,
        lesson_title=quiz_lesson.title,
        question_count=len(quiz_lesson.questions),
        questions=quiz_lesson.questions,
    )


# Grading is one request per answer with no server side session, so a client
# could call this endpoint repeatedly to discover the correct choice. Accepted
# for this feature; feature 006 adds the attempts table and makes an attempt
# single submission.
@router.post("/lessons/{slug}/quiz/answers", response_model=AnswerResponse)
def submit_answer(slug: str, answer: AnswerRequest, db: Session = Depends(get_db)):
    try:
        result = quiz_service.grade_answer(db, slug, answer.question_id, answer.choice_id)
    except quiz_service.InvalidChoiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if result is None:
        raise HTTPException(status_code=404, detail="Question not found")

    return AnswerResponse(correct=result.correct, correct_choice_id=result.correct_choice_id)
