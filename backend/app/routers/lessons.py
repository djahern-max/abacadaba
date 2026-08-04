from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.lesson import LessonDetail, LessonSummary, VideoUrlResponse
from app.services import lessons as lessons_service
from app.services import storage

VIDEO_URL_EXPIRES_IN = 3600

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


@router.get("/lessons/{slug}/video-url", response_model=VideoUrlResponse)
def get_video_url(slug: str, db: Session = Depends(get_db)):
    lesson = lessons_service.get_by_slug(db, slug)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if lesson.video_key is None:
        raise HTTPException(status_code=404, detail="This lesson has no video yet")

    try:
        url = storage.generate_presigned_get(lesson.video_key, expires_in=VIDEO_URL_EXPIRES_IN)
    except storage.StorageError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return VideoUrlResponse(url=url, expires_in=VIDEO_URL_EXPIRES_IN)
