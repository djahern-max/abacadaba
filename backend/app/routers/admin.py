from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_admin
from app.models.lesson import Lesson
from app.schemas.admin import (
    AdminChoice,
    AdminChoiceIn,
    AdminChoiceUpdate,
    AdminLesson,
    AdminLessonCreate,
    AdminLessonSummary,
    AdminLessonUpdate,
    AdminQuestion,
    AdminQuestionIn,
    AdminQuestionUpdate,
    MoveRequest,
    SetCorrectChoiceRequest,
)
from app.services import admin_content
from app.services import storage

router = APIRouter(dependencies=[Depends(require_admin)])

ALLOWED_CONTENT_TYPES = {
    "video/mp4": ".mp4",
    "video/webm": ".webm",
}


@router.get("/admin/lessons", response_model=list[AdminLessonSummary])
def list_lessons(db: Session = Depends(get_db)):
    return admin_content.list_lessons(db)


@router.post("/admin/lessons", response_model=AdminLesson, status_code=201)
def create_lesson(payload: AdminLessonCreate, db: Session = Depends(get_db)):
    try:
        lesson = admin_content.create_lesson(
            db, payload.title, payload.slug, payload.description, payload.duration_seconds
        )
    except admin_content.SlugTakenError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return admin_content.get_lesson(db, lesson.id)


@router.get("/admin/lessons/{lesson_id}", response_model=AdminLesson)
def get_lesson(lesson_id: int, db: Session = Depends(get_db)):
    try:
        return admin_content.get_lesson(db, lesson_id)
    except admin_content.LessonNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Lesson not found") from exc


@router.patch("/admin/lessons/{lesson_id}", response_model=AdminLesson)
def update_lesson(lesson_id: int, payload: AdminLessonUpdate, db: Session = Depends(get_db)):
    try:
        return admin_content.update_lesson(db, lesson_id, payload.model_dump(exclude_unset=True))
    except admin_content.LessonNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Lesson not found") from exc
    except admin_content.SlugTakenError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/admin/lessons/{lesson_id}", status_code=204)
def delete_lesson(lesson_id: int, db: Session = Depends(get_db)):
    try:
        admin_content.delete_lesson(db, lesson_id)
    except admin_content.LessonNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Lesson not found") from exc
    except admin_content.LessonHasAttemptsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/admin/lessons/{lesson_id}/publish", response_model=AdminLesson)
def publish_lesson(lesson_id: int, db: Session = Depends(get_db)):
    try:
        return admin_content.publish_lesson(db, lesson_id)
    except admin_content.LessonNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Lesson not found") from exc
    except admin_content.PublishValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors) from exc


@router.post("/admin/lessons/{lesson_id}/unpublish", response_model=AdminLesson)
def unpublish_lesson(lesson_id: int, db: Session = Depends(get_db)):
    try:
        return admin_content.unpublish_lesson(db, lesson_id)
    except admin_content.LessonNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Lesson not found") from exc


@router.post("/admin/lessons/{lesson_id}/questions", response_model=AdminQuestion, status_code=201)
def create_question(lesson_id: int, payload: AdminQuestionIn, db: Session = Depends(get_db)):
    try:
        return admin_content.create_question(db, lesson_id, payload.prompt)
    except admin_content.LessonNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Lesson not found") from exc


@router.patch("/admin/questions/{question_id}", response_model=AdminQuestion)
def update_question(question_id: int, payload: AdminQuestionUpdate, db: Session = Depends(get_db)):
    try:
        return admin_content.update_question(db, question_id, payload.model_dump(exclude_unset=True))
    except admin_content.QuestionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Question not found") from exc


@router.delete("/admin/questions/{question_id}", status_code=204)
def delete_question(question_id: int, db: Session = Depends(get_db)):
    try:
        admin_content.delete_question(db, question_id)
    except admin_content.QuestionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Question not found") from exc


@router.post("/admin/questions/{question_id}/move", response_model=None, status_code=204)
def move_question(question_id: int, payload: MoveRequest, db: Session = Depends(get_db)):
    try:
        admin_content.move_question(db, question_id, payload.direction)
    except admin_content.QuestionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Question not found") from exc


@router.post("/admin/questions/{question_id}/choices", response_model=AdminChoice, status_code=201)
def create_choice(question_id: int, payload: AdminChoiceIn, db: Session = Depends(get_db)):
    try:
        return admin_content.create_choice(db, question_id, payload.text, payload.is_correct)
    except admin_content.QuestionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Question not found") from exc


@router.patch("/admin/choices/{choice_id}", response_model=AdminChoice)
def update_choice(choice_id: int, payload: AdminChoiceUpdate, db: Session = Depends(get_db)):
    try:
        return admin_content.update_choice(db, choice_id, payload.model_dump(exclude_unset=True))
    except admin_content.ChoiceNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Choice not found") from exc


@router.delete("/admin/choices/{choice_id}", status_code=204)
def delete_choice(choice_id: int, db: Session = Depends(get_db)):
    try:
        admin_content.delete_choice(db, choice_id)
    except admin_content.ChoiceNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Choice not found") from exc


@router.post("/admin/choices/{choice_id}/move", response_model=None, status_code=204)
def move_choice(choice_id: int, payload: MoveRequest, db: Session = Depends(get_db)):
    try:
        admin_content.move_choice(db, choice_id, payload.direction)
    except admin_content.ChoiceNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Choice not found") from exc


@router.post("/admin/questions/{question_id}/correct-choice", response_model=None, status_code=204)
def set_correct_choice(question_id: int, payload: SetCorrectChoiceRequest, db: Session = Depends(get_db)):
    try:
        admin_content.set_correct_choice(db, question_id, payload.choice_id)
    except admin_content.QuestionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Question not found") from exc
    except admin_content.ChoiceNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/admin/lessons/{slug}/video")
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
