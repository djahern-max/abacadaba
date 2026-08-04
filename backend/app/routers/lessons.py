from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.lesson import LessonDetail, LessonSummary
from app.services import lessons as lessons_service

router = APIRouter()


@router.get("/lessons", response_model=list[LessonSummary])
def list_lessons(db: Session = Depends(get_db)):
    return lessons_service.list_published(db)


@router.get("/lessons/{slug}", response_model=LessonDetail)
def get_lesson(slug: str, db: Session = Depends(get_db)):
    lesson = lessons_service.get_by_slug(db, slug)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson
