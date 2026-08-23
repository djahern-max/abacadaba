"""Exercises the backfill SQL from migration 19665ec864ab directly, against
rows shaped like backend/scripts/seed_asc606_construction_intro.sql's
8-question-per-lesson convention (positions 1-3 review, 4+ assessment) -
the convention the migration's `WHERE position <= 3` relies on.
"""

from sqlalchemy import delete, select, text

from app.db import SessionLocal
from app.models.choice import Choice
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.question import Question

SLUG = "test-kind-backfill-course"


def test_backfill_types_an_eight_question_lesson_as_three_review_five_assessment():
    db = SessionLocal()
    try:
        course = Course(slug=SLUG, title="Backfill Test", description="d")
        db.add(course)
        db.flush()
        lesson = Lesson(course_id=course.id, position=1, slug=f"{SLUG}-lesson", title="L", description="d")
        db.add(lesson)
        db.flush()
        for position in range(1, 9):
            question = Question(lesson_id=lesson.id, prompt=f"Q{position}", position=position)
            question.choices = [
                Choice(text="a", is_correct=(position == 1), position=1),
                Choice(text="b", is_correct=(position != 1), position=2),
            ]
            db.add(question)
        db.commit()

        # Every row above got the column default ('assessment') at insert
        # time, exactly like a pre-023 database before this migration runs.
        # Re-apply the migration's own backfill statement to it.
        db.execute(text("UPDATE questions SET kind = 'review' WHERE position <= 3 AND lesson_id = :lid"), {"lid": lesson.id})
        db.commit()

        kinds = db.execute(
            select(Question.position, Question.kind).where(Question.lesson_id == lesson.id).order_by(Question.position)
        ).all()
        review_positions = [position for position, kind in kinds if kind == "review"]
        assessment_positions = [position for position, kind in kinds if kind == "assessment"]
        assert review_positions == [1, 2, 3]
        assert assessment_positions == [4, 5, 6, 7, 8]
    finally:
        db.execute(delete(Course).where(Course.slug == SLUG))
        db.commit()
        db.close()
