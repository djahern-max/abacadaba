import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.quiz import QuestionPublic, QuizPublic
from app.services import quiz as quiz_service
from app.services import lessons as lessons_service

router = APIRouter()


@router.get("/lessons/{slug}/quiz", response_model=QuizPublic)
def get_quiz(slug: str, attempt_id: uuid.UUID | None = None, db: Session = Depends(get_db)):
    lesson = lessons_service.get_by_slug(db, slug)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    quiz_lesson = quiz_service.get_quiz_for_lesson(db, slug)
    if quiz_lesson is None:
        raise HTTPException(status_code=404, detail="This lesson has no quiz yet")

    seed = None
    if attempt_id is not None:
        seed = quiz_service.get_attempt_shuffle_seed(db, attempt_id, quiz_lesson.id)
        if seed is None:
            raise HTTPException(status_code=404, detail="Attempt not found for this lesson")

    questions = quiz_lesson.questions
    if seed is not None:
        questions = quiz_service.shuffle_questions(questions, seed)

    question_payloads = []
    for question in questions:
        choices = question.choices
        if seed is not None:
            choices = quiz_service.shuffle_choices(choices, seed, question.id)
        question_payloads.append(
            QuestionPublic(id=question.id, prompt=question.prompt, position=question.position, choices=choices)
        )

    return QuizPublic(
        lesson_slug=quiz_lesson.slug,
        lesson_title=quiz_lesson.title,
        question_count=len(quiz_lesson.questions),
        questions=question_payloads,
    )
