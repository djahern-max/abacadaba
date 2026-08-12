from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.attempt import Attempt
from app.models.attempt_answer import AttemptAnswer
from app.models.choice import Choice
from app.models.lesson import Lesson
from app.models.question import Question


@dataclass
class CourseStatsData:
    attempts_started: int
    attempts_completed: int
    completion_rate: float
    pass_rate: float | None
    mean_score: float | None


@dataclass
class QuestionStatData:
    question_id: int
    lesson_title: str
    prompt: str
    position: int
    answered: int
    pct_correct: float | None


@dataclass
class ChoiceStatData:
    choice_id: int
    text: str
    position: int
    is_correct: bool
    picked_count: int


@dataclass
class DropoffPointData:
    question_id: int
    lesson_title: str
    position: int
    attempts_reached: int


def course_stats(db: Session, course_id: int) -> CourseStatsData:
    stmt = select(
        func.count(Attempt.id).label("started"),
        func.count(Attempt.id).filter(Attempt.completed_at.is_not(None)).label("completed"),
        func.count(Attempt.id)
        .filter(Attempt.completed_at.is_not(None), Attempt.passed.is_(True))
        .label("passed"),
        func.avg(Attempt.score).filter(Attempt.completed_at.is_not(None)).label("mean_score"),
    ).where(Attempt.course_id == course_id)
    row = db.execute(stmt).one()

    completion_rate = (row.completed / row.started) if row.started else 0.0
    pass_rate = (row.passed / row.completed) if row.completed else None
    mean_score = float(row.mean_score) if row.mean_score is not None else None

    return CourseStatsData(
        attempts_started=row.started,
        attempts_completed=row.completed,
        completion_rate=completion_rate,
        pass_rate=pass_rate,
        mean_score=mean_score,
    )


def question_stats(db: Session, course_id: int) -> list[QuestionStatData]:
    answered = func.count(AttemptAnswer.id)
    correct = func.count(AttemptAnswer.id).filter(AttemptAnswer.is_correct.is_(True))
    pct_correct = (correct * 100.0) / func.nullif(answered, 0)

    stmt = (
        select(
            Question.id,
            Lesson.title.label("lesson_title"),
            Question.prompt,
            Question.position,
            answered.label("answered"),
            pct_correct.label("pct_correct"),
        )
        .select_from(Question)
        .join(Lesson, Lesson.id == Question.lesson_id)
        .outerjoin(AttemptAnswer, AttemptAnswer.question_id == Question.id)
        .where(Lesson.course_id == course_id)
        .group_by(Question.id, Lesson.title)
        .order_by(pct_correct.asc().nulls_last())
    )
    rows = db.execute(stmt).all()
    return [
        QuestionStatData(
            question_id=row.id,
            lesson_title=row.lesson_title,
            prompt=row.prompt,
            position=row.position,
            answered=row.answered,
            pct_correct=float(row.pct_correct) if row.pct_correct is not None else None,
        )
        for row in rows
    ]


def choice_distribution(db: Session, question_id: int) -> list[ChoiceStatData]:
    stmt = (
        select(
            Choice.id,
            Choice.text,
            Choice.position,
            Choice.is_correct,
            func.count(AttemptAnswer.id).label("picked_count"),
        )
        .select_from(Choice)
        .outerjoin(AttemptAnswer, AttemptAnswer.choice_id == Choice.id)
        .where(Choice.question_id == question_id)
        .group_by(Choice.id)
        .order_by(Choice.position)
    )
    rows = db.execute(stmt).all()
    return [
        ChoiceStatData(
            choice_id=row.id,
            text=row.text,
            position=row.position,
            is_correct=row.is_correct,
            picked_count=row.picked_count,
        )
        for row in rows
    ]


def dropoff(db: Session, course_id: int) -> list[DropoffPointData]:
    stmt = (
        select(
            Question.id,
            Lesson.title.label("lesson_title"),
            Question.position,
            func.count(func.distinct(AttemptAnswer.attempt_id)).label("attempts_reached"),
        )
        .select_from(Question)
        .join(Lesson, Lesson.id == Question.lesson_id)
        .outerjoin(AttemptAnswer, AttemptAnswer.question_id == Question.id)
        .where(Lesson.course_id == course_id)
        .group_by(Question.id, Lesson.id, Lesson.title)
        .order_by(Lesson.position, Question.position)
    )
    rows = db.execute(stmt).all()
    return [
        DropoffPointData(
            question_id=row.id,
            lesson_title=row.lesson_title,
            position=row.position,
            attempts_reached=row.attempts_reached,
        )
        for row in rows
    ]
