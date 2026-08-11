import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user, get_viewer_id
from app.models.user import User
from app.schemas.watch import HeartbeatRequest, WatchProgressResponse
from app.services import lessons as lessons_service
from app.services import watch as watch_service

router = APIRouter()


def _get_published_lesson_or_404(db: Session, slug: str):
    lesson = lessons_service.get_by_slug(db, slug)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


def _to_response(progress: watch_service.WatchProgressData) -> WatchProgressResponse:
    return WatchProgressResponse(
        watched_seconds=progress.watched_seconds,
        required_seconds=progress.required_seconds,
        duration_seconds=progress.duration_seconds,
        ratio=progress.ratio,
        unlocked=progress.unlocked,
    )


@router.post("/lessons/{slug}/watch", response_model=WatchProgressResponse)
def post_heartbeat(
    slug: str,
    payload: HeartbeatRequest,
    db: Session = Depends(get_db),
    viewer_id: uuid.UUID = Depends(get_viewer_id),
    user: User | None = Depends(get_current_user),
):
    lesson = _get_published_lesson_or_404(db, slug)
    try:
        progress = watch_service.record_heartbeat(
            db, lesson, viewer_id, user.id if user else None, payload.position
        )
    except watch_service.RateLimitedError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc

    return _to_response(progress)


@router.get("/lessons/{slug}/watch", response_model=WatchProgressResponse)
def get_watch_progress(
    slug: str,
    db: Session = Depends(get_db),
    viewer_id: uuid.UUID = Depends(get_viewer_id),
    user: User | None = Depends(get_current_user),
):
    lesson = _get_published_lesson_or_404(db, slug)
    progress = watch_service.get_progress(db, lesson, viewer_id, user.id if user else None)
    return _to_response(progress)
