from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.services import og as og_service

router = APIRouter()


# Path matches abacadaba.conf's commented-out Open Graph crawler branch
# exactly: nginx proxies /__og/courses/{slug} to /api/v1/og/courses/{slug}
# on this service. See DEPLOYMENT.md.
@router.get("/og/courses/{slug}", response_class=HTMLResponse)
def get_course_og_preview(slug: str, db: Session = Depends(get_db)):
    return og_service.course_preview_html(db, slug)
