from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_admin
from app.models.lesson import Lesson
from app.schemas.analytics import LessonAnalytics, QuestionChoiceDistribution
from app.services import analytics

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/admin/lessons/{lesson_id}/stats", response_model=LessonAnalytics)
def get_lesson_stats(lesson_id: int, db: Session = Depends(get_db)):
    if db.get(Lesson, lesson_id) is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    questions = analytics.question_stats(db, lesson_id)
    return LessonAnalytics(
        lesson_stats=analytics.lesson_stats(db, lesson_id),
        question_stats=questions,
        choice_distribution=[
            QuestionChoiceDistribution(
                question_id=question.question_id,
                choices=analytics.choice_distribution(db, question.question_id),
            )
            for question in sorted(questions, key=lambda q: q.position)
        ],
        dropoff=analytics.dropoff(db, lesson_id),
    )
