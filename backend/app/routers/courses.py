import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user, get_viewer_id
from app.models.course import Course
from app.models.user import User
from app.schemas.attempt import AttemptStart
from app.schemas.course import CourseDetail, CourseSummary, LessonSegmentDetail
from app.schemas.lesson import ThumbnailUrlResponse, VideoUrlResponse
from app.schemas.quiz import QuestionPublic, QuizPublic
from app.schemas.watch import (
    CourseWatchStatusResponse,
    HeartbeatRequest,
    LessonWatchStatusResponse,
    WatchProgressResponse,
)
from app.services import attempts as attempts_service
from app.services import courses as courses_service
from app.services import quiz as quiz_service
from app.services import storage
from app.services import watch as watch_service

VIDEO_URL_EXPIRES_IN = 3600
THUMBNAIL_URL_EXPIRES_IN = 3600

router = APIRouter()


@router.get("/courses", response_model=list[CourseSummary])
def list_courses(db: Session = Depends(get_db)):
    return courses_service.list_published(db)


@router.get("/courses/{slug}", response_model=CourseDetail)
def get_course(slug: str, db: Session = Depends(get_db)):
    course = courses_service.get_with_lessons(db, slug)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("/courses/{slug}/thumbnail-url", response_model=ThumbnailUrlResponse)
def get_course_thumbnail_url(slug: str, db: Session = Depends(get_db)):
    course = courses_service.get_by_slug(db, slug)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.thumbnail_key is None:
        raise HTTPException(status_code=404, detail="This course has no thumbnail yet")

    try:
        url = storage.generate_presigned_get(course.thumbnail_key, expires_in=THUMBNAIL_URL_EXPIRES_IN)
    except storage.StorageError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return ThumbnailUrlResponse(url=url, expires_in=THUMBNAIL_URL_EXPIRES_IN)


@router.get("/courses/{slug}/lessons/{lesson_slug}", response_model=LessonSegmentDetail)
def get_lesson_segment(slug: str, lesson_slug: str, db: Session = Depends(get_db)):
    segment = courses_service.get_lesson_in_course(db, slug, lesson_slug)
    if segment is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return segment


@router.get("/courses/{slug}/lessons/{lesson_slug}/video-url", response_model=VideoUrlResponse)
def get_lesson_video_url(slug: str, lesson_slug: str, db: Session = Depends(get_db)):
    lesson = courses_service.get_published_lesson(db, slug, lesson_slug)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if lesson.video_key is None:
        raise HTTPException(status_code=404, detail="This lesson has no video yet")

    try:
        url = storage.generate_presigned_get(lesson.video_key, expires_in=VIDEO_URL_EXPIRES_IN)
    except storage.StorageError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return VideoUrlResponse(url=url, expires_in=VIDEO_URL_EXPIRES_IN)


@router.get("/courses/{slug}/lessons/{lesson_slug}/thumbnail-url", response_model=ThumbnailUrlResponse)
def get_lesson_thumbnail_url(slug: str, lesson_slug: str, db: Session = Depends(get_db)):
    lesson = courses_service.get_published_lesson(db, slug, lesson_slug)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if lesson.thumbnail_key is None:
        raise HTTPException(status_code=404, detail="This lesson has no thumbnail yet")

    try:
        url = storage.generate_presigned_get(lesson.thumbnail_key, expires_in=THUMBNAIL_URL_EXPIRES_IN)
    except storage.StorageError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return ThumbnailUrlResponse(url=url, expires_in=THUMBNAIL_URL_EXPIRES_IN)


def _to_progress_response(progress: watch_service.WatchProgressData) -> WatchProgressResponse:
    return WatchProgressResponse(
        watched_seconds=progress.watched_seconds,
        required_seconds=progress.required_seconds,
        duration_seconds=progress.duration_seconds,
        ratio=progress.ratio,
        unlocked=progress.unlocked,
    )


@router.post("/courses/{slug}/lessons/{lesson_slug}/watch", response_model=WatchProgressResponse)
def post_lesson_heartbeat(
    slug: str,
    lesson_slug: str,
    payload: HeartbeatRequest,
    db: Session = Depends(get_db),
    viewer_id: uuid.UUID = Depends(get_viewer_id),
    user: User | None = Depends(get_current_user),
):
    lesson = courses_service.get_published_lesson(db, slug, lesson_slug)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    try:
        progress = watch_service.record_heartbeat(
            db, lesson, viewer_id, user.id if user else None, payload.position
        )
    except watch_service.RateLimitedError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc

    return _to_progress_response(progress)


@router.get("/courses/{slug}/lessons/{lesson_slug}/watch", response_model=WatchProgressResponse)
def get_lesson_watch_progress(
    slug: str,
    lesson_slug: str,
    db: Session = Depends(get_db),
    viewer_id: uuid.UUID = Depends(get_viewer_id),
    user: User | None = Depends(get_current_user),
):
    lesson = courses_service.get_published_lesson(db, slug, lesson_slug)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    progress = watch_service.get_progress(db, lesson, viewer_id, user.id if user else None)
    return _to_progress_response(progress)


@router.get("/courses/{slug}/watch-status", response_model=CourseWatchStatusResponse)
def get_course_watch_status(
    slug: str,
    db: Session = Depends(get_db),
    viewer_id: uuid.UUID = Depends(get_viewer_id),
    user: User | None = Depends(get_current_user),
):
    course = db.execute(select(Course).where(Course.slug == slug, Course.is_published.is_(True))).scalar_one_or_none()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    status = watch_service.course_watch_status(db, course, viewer_id, user.id if user else None)
    return CourseWatchStatusResponse(
        gate_met=status.gate_met,
        lessons=[
            LessonWatchStatusResponse(
                lesson_slug=item.lesson_slug,
                lesson_title=item.lesson_title,
                position=item.position,
                progress=_to_progress_response(item.progress),
            )
            for item in status.lessons
        ],
    )


@router.get("/courses/{slug}/quiz", response_model=QuizPublic)
def get_quiz(slug: str, attempt_id: uuid.UUID | None = None, db: Session = Depends(get_db)):
    course_quiz = quiz_service.get_quiz_for_course(db, slug)
    if course_quiz is None:
        raise HTTPException(status_code=404, detail="This course has no assessment yet")

    seed = None
    course_id = db.execute(select(Course.id).where(Course.slug == slug)).scalar_one()
    if attempt_id is not None:
        seed = quiz_service.get_attempt_shuffle_seed(db, attempt_id, course_id)
        if seed is None:
            raise HTTPException(status_code=404, detail="Attempt not found for this course")

    questions = course_quiz.questions
    if seed is not None:
        questions = quiz_service.shuffle_questions(questions, seed)

    question_payloads = []
    for index, question in enumerate(questions, start=1):
        choices = question.choices
        if seed is not None:
            choices = quiz_service.shuffle_choices(choices, seed, question.id)
        # `position` here is the question's 1-based place in the served
        # (possibly shuffled) order, not its authored `Question.position` —
        # the progress bar counts through served order, so the two must match.
        question_payloads.append(
            QuestionPublic(id=question.id, prompt=question.prompt, position=index, choices=choices)
        )

    return QuizPublic(
        course_slug=course_quiz.course_slug,
        course_title=course_quiz.course_title,
        question_count=len(course_quiz.questions),
        questions=question_payloads,
    )


@router.post("/courses/{slug}/attempts", response_model=AttemptStart, status_code=201)
def start_attempt(
    slug: str,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
    viewer_id: uuid.UUID = Depends(get_viewer_id),
):
    try:
        result = attempts_service.start_attempt(db, slug, user, viewer_id)
    except attempts_service.CourseExpiredError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except attempts_service.NotAuthenticatedError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except attempts_service.WatchRequirementNotMetError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except attempts_service.MaxAttemptsExceededError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except attempts_service.RetakeCooldownError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="This course has no assessment yet")

    return AttemptStart(
        attempt_id=result.attempt_id, course_slug=result.course_slug, question_count=result.question_count
    )
