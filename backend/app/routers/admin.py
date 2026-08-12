import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_admin
from app.models.course import Course
from app.models.lesson import Lesson
from app.schemas.admin import (
    AdminChoice,
    AdminChoiceIn,
    AdminChoiceUpdate,
    AdminCourse,
    AdminCourseCreate,
    AdminCourseSummary,
    AdminCourseUpdate,
    AdminLesson,
    AdminLessonCreate,
    AdminLessonUpdate,
    AdminObjective,
    AdminObjectiveIn,
    AdminObjectiveUpdate,
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

ALLOWED_THUMBNAIL_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

THUMBNAIL_PIL_FORMATS = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}

MAX_THUMBNAIL_BYTES = 2 * 1024 * 1024

TARGET_ASPECT_RATIO = 16 / 9
ASPECT_RATIO_TOLERANCE = 0.02


# --- courses -----------------------------------------------------------------


@router.get("/admin/courses", response_model=list[AdminCourseSummary])
def list_courses(db: Session = Depends(get_db)):
    return admin_content.list_courses(db)


@router.post("/admin/courses", response_model=AdminCourse, status_code=201)
def create_course(payload: AdminCourseCreate, db: Session = Depends(get_db)):
    try:
        course = admin_content.create_course(db, payload.title, payload.slug, payload.description)
    except admin_content.SlugTakenError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return admin_content.get_course(db, course.id)


@router.get("/admin/courses/{course_id}", response_model=AdminCourse)
def get_course(course_id: int, db: Session = Depends(get_db)):
    try:
        return admin_content.get_course(db, course_id)
    except admin_content.CourseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Course not found") from exc


@router.patch("/admin/courses/{course_id}", response_model=AdminCourse)
def update_course(course_id: int, payload: AdminCourseUpdate, db: Session = Depends(get_db)):
    try:
        return admin_content.update_course(db, course_id, payload.model_dump(exclude_unset=True))
    except admin_content.CourseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Course not found") from exc
    except admin_content.SlugTakenError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/admin/courses/{course_id}", status_code=204)
def delete_course(course_id: int, db: Session = Depends(get_db)):
    try:
        admin_content.delete_course(db, course_id)
    except admin_content.CourseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Course not found") from exc
    except admin_content.CourseHasAttemptsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/admin/courses/{course_id}/publish", response_model=None)
def publish_course(course_id: int, dry_run: bool = False, db: Session = Depends(get_db)):
    try:
        if dry_run:
            return {"errors": admin_content.check_publish_course(db, course_id)}
        course = admin_content.publish_course(db, course_id)
        return AdminCourse.model_validate(course)
    except admin_content.CourseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Course not found") from exc
    except admin_content.PublishValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors) from exc


@router.post("/admin/courses/{course_id}/unpublish", response_model=AdminCourse)
def unpublish_course(course_id: int, db: Session = Depends(get_db)):
    try:
        return admin_content.unpublish_course(db, course_id)
    except admin_content.CourseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Course not found") from exc


@router.post("/admin/courses/{course_id}/thumbnail")
async def upload_course_thumbnail(course_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    ext = ALLOWED_THUMBNAIL_CONTENT_TYPES.get(file.content_type)
    if ext is None:
        raise HTTPException(status_code=400, detail="Thumbnail must be JPEG, PNG, or WebP")

    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    contents = await file.read()
    if len(contents) > MAX_THUMBNAIL_BYTES:
        raise HTTPException(status_code=400, detail="Thumbnail must be 2 MB or smaller")

    try:
        with Image.open(io.BytesIO(contents)) as image:
            image.load()
            actual_format = image.format
            width, height = image.size
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="Thumbnail must be JPEG, PNG, or WebP") from None

    if actual_format != THUMBNAIL_PIL_FORMATS[file.content_type]:
        raise HTTPException(status_code=400, detail="Thumbnail must be JPEG, PNG, or WebP")

    warning = None
    if abs(width / height - TARGET_ASPECT_RATIO) > ASPECT_RATIO_TOLERANCE:
        warning = "This image isn't 16:9, so it may not display cleanly."

    old_key = course.thumbnail_key
    key = f"courses/{course.slug}-thumb{ext}"
    try:
        storage.upload_fileobj(io.BytesIO(contents), key, file.content_type)
    except storage.StorageError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if old_key and old_key != key:
        try:
            storage.delete_object(old_key)
        except storage.StorageError:
            pass

    course.thumbnail_key = key
    db.commit()

    return {"thumbnail_key": course.thumbnail_key, "warning": warning}


# --- learning objectives ------------------------------------------------------


@router.post("/admin/courses/{course_id}/objectives", response_model=AdminObjective, status_code=201)
def create_objective(course_id: int, payload: AdminObjectiveIn, db: Session = Depends(get_db)):
    try:
        return admin_content.create_objective(db, course_id, payload.text)
    except admin_content.CourseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Course not found") from exc


@router.patch("/admin/objectives/{objective_id}", response_model=AdminObjective)
def update_objective(objective_id: int, payload: AdminObjectiveUpdate, db: Session = Depends(get_db)):
    try:
        return admin_content.update_objective(db, objective_id, payload.model_dump(exclude_unset=True))
    except admin_content.ObjectiveNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Learning objective not found") from exc


@router.delete("/admin/objectives/{objective_id}", status_code=204)
def delete_objective(objective_id: int, db: Session = Depends(get_db)):
    try:
        admin_content.delete_objective(db, objective_id)
    except admin_content.ObjectiveNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Learning objective not found") from exc


@router.post("/admin/objectives/{objective_id}/move", response_model=None, status_code=204)
def move_objective(objective_id: int, payload: MoveRequest, db: Session = Depends(get_db)):
    try:
        admin_content.move_objective(db, objective_id, payload.direction)
    except admin_content.ObjectiveNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Learning objective not found") from exc


# --- lessons -----------------------------------------------------------------


@router.post("/admin/courses/{course_id}/lessons", response_model=AdminLesson, status_code=201)
def create_lesson(course_id: int, payload: AdminLessonCreate, db: Session = Depends(get_db)):
    try:
        lesson = admin_content.create_lesson(
            db, course_id, payload.title, payload.slug, payload.description, payload.duration_seconds
        )
    except admin_content.CourseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Course not found") from exc
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


@router.post("/admin/lessons/{lesson_id}/move", response_model=None, status_code=204)
def move_lesson(lesson_id: int, payload: MoveRequest, db: Session = Depends(get_db)):
    try:
        admin_content.move_lesson(db, lesson_id, payload.direction)
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


@router.post("/admin/lessons/{lesson_id}/thumbnail")
async def upload_lesson_thumbnail(
    lesson_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    ext = ALLOWED_THUMBNAIL_CONTENT_TYPES.get(file.content_type)
    if ext is None:
        raise HTTPException(
            status_code=400,
            detail="Thumbnail must be JPEG, PNG, or WebP",
        )

    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    contents = await file.read()
    if len(contents) > MAX_THUMBNAIL_BYTES:
        raise HTTPException(status_code=400, detail="Thumbnail must be 2 MB or smaller")

    # The declared content type comes from the browser's file-extension guess,
    # not the actual bytes, so a renamed PDF would otherwise sail through.
    try:
        with Image.open(io.BytesIO(contents)) as image:
            image.load()
            actual_format = image.format
            width, height = image.size
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="Thumbnail must be JPEG, PNG, or WebP") from None

    if actual_format != THUMBNAIL_PIL_FORMATS[file.content_type]:
        raise HTTPException(status_code=400, detail="Thumbnail must be JPEG, PNG, or WebP")

    warning = None
    if abs(width / height - TARGET_ASPECT_RATIO) > ASPECT_RATIO_TOLERANCE:
        warning = "This image isn't 16:9, so it may not display cleanly."

    old_key = lesson.thumbnail_key
    key = f"lessons/{lesson.slug}-thumb{ext}"
    try:
        storage.upload_fileobj(io.BytesIO(contents), key, file.content_type)
    except storage.StorageError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if old_key and old_key != key:
        try:
            storage.delete_object(old_key)
        except storage.StorageError:
            pass

    lesson.thumbnail_key = key
    db.commit()

    return {"thumbnail_key": lesson.thumbnail_key, "warning": warning}
