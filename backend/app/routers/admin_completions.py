from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_admin
from app.schemas.completions import AdminCompletionRow
from app.services import completions as completions_service

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/admin/completions", response_model=list[AdminCompletionRow])
def get_completions(
    course_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    passed: bool | None = None,
    db: Session = Depends(get_db),
):
    rows = completions_service.list_completions(
        db, course_id=course_id, start_date=start_date, end_date=end_date, passed=passed
    )
    return [AdminCompletionRow.model_validate(row) for row in rows]


@router.get("/admin/completions.csv")
def get_completions_csv(
    course_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    passed: bool | None = None,
    db: Session = Depends(get_db),
):
    rows = completions_service.list_completions(
        db, course_id=course_id, start_date=start_date, end_date=end_date, passed=passed
    )
    return StreamingResponse(
        completions_service.stream_csv(rows),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="completions.csv"'},
    )
