import secrets

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.lesson import Lesson
from app.services import storage

router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    "video/mp4": ".mp4",
    "video/webm": ".webm",
}

# The shared secret header is a stopgap so uploads aren't wide open. It is
# replaced by real auth in feature 008.


def require_upload_secret(x_upload_secret: str = Header(default="")):
    if not secrets.compare_digest(x_upload_secret, settings.upload_secret):
        raise HTTPException(status_code=401, detail="Invalid upload secret")


@router.post(
    "/admin/lessons/{slug}/video",
    dependencies=[Depends(require_upload_secret)],
)
async def upload_lesson_video(
    slug: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    ext = ALLOWED_CONTENT_TYPES.get(file.content_type)
    if ext is None:
        raise HTTPException(
            status_code=400,
            detail="Video must be video/mp4 or video/webm",
        )

    lesson = db.execute(select(Lesson).where(Lesson.slug == slug)).scalar_one_or_none()
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    key = f"lessons/{slug}{ext}"
    try:
        storage.upload_fileobj(file.file, key, file.content_type)
    except storage.StorageError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    lesson.video_key = key
    db.commit()

    return {"video_key": lesson.video_key}
