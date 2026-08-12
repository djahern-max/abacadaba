from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_admin
from app.models.course import Course
from app.schemas.analytics import CourseAnalytics, QuestionChoiceDistribution
from app.services import analytics

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/admin/courses/{course_id}/stats", response_model=CourseAnalytics)
def get_course_stats(course_id: int, db: Session = Depends(get_db)):
    if db.get(Course, course_id) is None:
        raise HTTPException(status_code=404, detail="Course not found")

    questions = analytics.question_stats(db, course_id)
    return CourseAnalytics(
        course_stats=analytics.course_stats(db, course_id),
        question_stats=questions,
        choice_distribution=[
            QuestionChoiceDistribution(
                question_id=question.question_id,
                choices=analytics.choice_distribution(db, question.question_id),
            )
            for question in questions
        ],
        dropoff=analytics.dropoff(db, course_id),
    )
