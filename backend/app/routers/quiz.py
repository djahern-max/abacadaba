from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.quiz import QuizPublic
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
