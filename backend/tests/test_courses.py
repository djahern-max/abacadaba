import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db import SessionLocal
from app.main import app
from app.models.choice import Choice
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.question import Question
from app.models.session import Session as SessionModel
from app.models.user import User
from app.models.watch_progress import WatchProgress

client = TestClient(app)

PUBLISHED_SLUG = "test-published-course"
UNPUBLISHED_SLUG = "test-unpublished-course"
SINGLE_LESSON_SLUG = "test-single-lesson-course"
EXPIRED_SLUG = "test-expired-course"
ALL_TEST_SLUGS = [PUBLISHED_SLUG, UNPUBLISHED_SLUG, SINGLE_LESSON_SLUG, EXPIRED_SLUG]


@pytest.fixture(autouse=True)
def seed_test_courses():
    db = SessionLocal()
    published = Course(
        slug=PUBLISHED_SLUG,
        title="Published Test Course",
        description="A course used for testing the courses endpoints.",
        is_published=True,
    )
    db.add(published)
    db.flush()
    db.add(
        Lesson(
            course_id=published.id,
            position=1,
            slug=f"{PUBLISHED_SLUG}-lesson-one",
            title="Segment One",
            description="First segment.",
            duration_seconds=300,
            is_published=True,
        )
    )
    db.add(
        Lesson(
            course_id=published.id,
            position=2,
            slug=f"{PUBLISHED_SLUG}-lesson-two",
            title="Segment Two",
            description="Second segment, unpublished.",
            duration_seconds=300,
            is_published=False,
        )
    )
    db.add(
        Course(
            slug=UNPUBLISHED_SLUG,
            title="Unpublished Test Course",
            description="A course that should never appear in the public API.",
            is_published=False,
        )
    )
    single_lesson_course = Course(
        slug=SINGLE_LESSON_SLUG,
        title="Single Lesson Test Course",
        description="A one-lesson course used to test the collapsed public payload.",
        is_published=True,
        prerequisites="None",
        advance_preparation="None",
    )
    db.add(single_lesson_course)
    db.flush()
    db.add(
        Lesson(
            course_id=single_lesson_course.id,
            position=1,
            slug=f"{SINGLE_LESSON_SLUG}-lesson-one",
            title="Single Lesson Test Course",
            description="",
            duration_seconds=300,
            is_published=True,
            video_key="lessons/should-never-leak.mp4",
        )
    )
    db.add(
        Course(
            slug=EXPIRED_SLUG,
            title="Expired Test Course",
            description="A published course past its 9.02.2 expiration date.",
            is_published=True,
            expires_on=date.today() - timedelta(days=1),
        )
    )
    db.commit()
    db.close()

    yield

    db = SessionLocal()
    db.execute(delete(Course).where(Course.slug.in_(ALL_TEST_SLUGS)))
    db.commit()
    db.close()


def test_list_courses_returns_list():
    response = client.get("/api/v1/courses")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_unpublished_course_not_in_list():
    response = client.get("/api/v1/courses")
    slugs = [course["slug"] for course in response.json()]
    assert PUBLISHED_SLUG in slugs
    assert UNPUBLISHED_SLUG not in slugs


def test_list_item_reports_published_lesson_count():
    response = client.get("/api/v1/courses")
    course = next(c for c in response.json() if c["slug"] == PUBLISHED_SLUG)
    assert course["lesson_count"] == 1


def test_get_course_by_slug():
    response = client.get(f"/api/v1/courses/{PUBLISHED_SLUG}")
    assert response.status_code == 200
    assert response.json()["slug"] == PUBLISHED_SLUG


def test_course_detail_only_lists_published_lessons_in_order():
    response = client.get(f"/api/v1/courses/{PUBLISHED_SLUG}")
    body = response.json()
    assert len(body["lessons"]) == 1
    assert body["lessons"][0]["slug"] == f"{PUBLISHED_SLUG}-lesson-one"


def test_unknown_slug_returns_404():
    response = client.get("/api/v1/courses/does-not-exist")
    assert response.status_code == 404


def test_unpublished_course_returns_404():
    response = client.get(f"/api/v1/courses/{UNPUBLISHED_SLUG}")
    assert response.status_code == 404


# LEAK TEST (feature 019a): the collapsed single-lesson page reads its video
# from the same public course payload that a signed-out visitor can fetch.
# That payload must disclose the 020 pre-enrollment fields but never the
# lesson's video_key or a playable URL - only the gated video-url endpoint
# may hand that out.
def test_single_lesson_course_payload_discloses_metadata_and_omits_video_url():
    response = client.get(f"/api/v1/courses/{SINGLE_LESSON_SLUG}")
    assert response.status_code == 200
    body = response.json()

    assert len(body["lessons"]) == 1
    lesson = body["lessons"][0]
    assert "video_key" not in lesson
    assert "video_url" not in lesson
    assert not any("video" in key for key in lesson.keys())

    assert body["program_level"] == "basic"
    assert body["field_of_study"]
    assert body["prerequisites"] == "None"
    assert body["advance_preparation"] == "None"


# --- expiration (feature 026, 9.02.2) ----------------------------------------


def test_expired_course_does_not_appear_in_the_public_list():
    response = client.get("/api/v1/courses")
    slugs = [course["slug"] for course in response.json()]
    assert EXPIRED_SLUG not in slugs


def test_expired_course_detail_page_stays_reachable_not_404():
    # 9.02.2: "not found" is a lie - a bookmarked expired course still
    # resolves and discloses why, rather than being pulled out from under
    # anyone (the same reasoning feature 021 applied to a stale review).
    response = client.get(f"/api/v1/courses/{EXPIRED_SLUG}")
    assert response.status_code == 200
    assert response.json()["expires_on"] == str(date.today() - timedelta(days=1))


# --- assessment state on the segment page (feature 028) ---------------------
# The segment endpoint's assessment_unlocked/assessment_outstanding_lesson
# fields must agree with what /watch-status already reports for the same
# user on the same course - see current-feature.md, "Two implementations of
# 'is the assessment unlocked' will diverge."

COMPLETION_PATH_SLUG = "test-completion-path-course"
COMPLETION_PATH_LESSON_1 = f"{COMPLETION_PATH_SLUG}-lesson-1"
COMPLETION_PATH_LESSON_2 = f"{COMPLETION_PATH_SLUG}-lesson-2"
COMPLETION_PATH_MEMBER_EMAIL = "completion-path-member@example.com"
COMPLETION_PATH_ADMIN_EMAIL = "completion-path-admin@example.com"
COMPLETION_PATH_PASSWORD = "correct-horse-battery"


@pytest.fixture
def completion_path_course():
    client.cookies.clear()
    db = SessionLocal()
    course = Course(
        slug=COMPLETION_PATH_SLUG,
        title="Completion Path Test Course",
        description="A two-segment course used to test the segment page's assessment state.",
        is_published=True,
    )
    db.add(course)
    db.flush()
    lesson_slugs = [COMPLETION_PATH_LESSON_1, COMPLETION_PATH_LESSON_2]
    for position, slug in enumerate(lesson_slugs, start=1):
        lesson = Lesson(
            course_id=course.id,
            position=position,
            slug=slug,
            title=f"Segment {position}",
            description="d",
            duration_seconds=100,
            is_published=True,
        )
        db.add(lesson)
        db.flush()
        question = Question(lesson_id=lesson.id, prompt="Only question?", position=1)
        question.choices = [
            Choice(text="Right", is_correct=True, position=1),
            Choice(text="Wrong", is_correct=False, position=2),
        ]
        db.add(question)
    db.commit()
    db.close()

    yield lesson_slugs

    client.cookies.clear()
    db = SessionLocal()
    emails = [COMPLETION_PATH_MEMBER_EMAIL, COMPLETION_PATH_ADMIN_EMAIL]
    user_ids = select(User.id).where(User.email.in_(emails))
    db.execute(delete(SessionModel).where(SessionModel.user_id.in_(user_ids)))
    db.execute(delete(User).where(User.email.in_(emails)))
    db.execute(delete(Course).where(Course.slug == COMPLETION_PATH_SLUG))
    db.commit()
    db.close()


def _register_and_login(email, is_admin=False):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": COMPLETION_PATH_PASSWORD, "display_name": "Completion Path Tester"},
    )
    db = SessionLocal()
    user = db.execute(select(User).where(User.email == email)).scalar_one()
    if is_admin:
        user.is_admin = True
        db.commit()
    user_id = user.id
    db.close()
    return user_id


def _set_watch_progress(viewer_id, lesson_slug, watched_seconds):
    db = SessionLocal()
    lesson_id = db.execute(select(Lesson.id).where(Lesson.slug == lesson_slug)).scalar_one()
    db.add(WatchProgress(lesson_id=lesson_id, viewer_id=viewer_id, watched_seconds=watched_seconds))
    db.commit()
    db.close()


def test_course_detail_reports_pass_ratio_and_assessment_question_count(completion_path_course):
    response = client.get(f"/api/v1/courses/{COMPLETION_PATH_SLUG}")
    body = response.json()
    assert float(body["pass_ratio"]) == 0.70
    assert body["assessment_question_count"] == 2


def test_segment_reports_assessment_unlocked_on_middle_and_last_segment_when_fully_watched(completion_path_course):
    lesson_slugs = completion_path_course
    client.get(f"/api/v1/courses/{COMPLETION_PATH_SLUG}/lessons/{lesson_slugs[0]}/watch")
    viewer_id = uuid.UUID(client.cookies["viewer_id"])
    for slug in lesson_slugs:
        _set_watch_progress(viewer_id, slug, 90)  # duration 100 * default ratio 0.9
    _register_and_login(COMPLETION_PATH_MEMBER_EMAIL)  # claims the anonymous progress by viewer_id

    for slug in lesson_slugs:
        segment = client.get(f"/api/v1/courses/{COMPLETION_PATH_SLUG}/lessons/{slug}").json()
        assert segment["assessment_unlocked"] is True
        assert segment["assessment_outstanding_lesson"] is None


def test_segment_reports_locked_and_names_outstanding_segment_when_partly_watched(completion_path_course):
    lesson_slugs = completion_path_course
    client.get(f"/api/v1/courses/{COMPLETION_PATH_SLUG}/lessons/{lesson_slugs[0]}/watch")
    viewer_id = uuid.UUID(client.cookies["viewer_id"])
    _set_watch_progress(viewer_id, lesson_slugs[0], 90)
    _set_watch_progress(viewer_id, lesson_slugs[1], 10)  # below the 90-second threshold
    _register_and_login(COMPLETION_PATH_MEMBER_EMAIL)

    # Ground truth from the endpoint CourseDetail already relies on - the
    # segment payload must agree with this, not with a hardcoded name.
    watch_status = client.get(f"/api/v1/courses/{COMPLETION_PATH_SLUG}/watch-status").json()
    assert watch_status["gate_met"] is False
    outstanding_title = next(
        item["lesson_title"] for item in watch_status["lessons"] if not item["progress"]["unlocked"]
    )

    for slug in lesson_slugs:
        segment = client.get(f"/api/v1/courses/{COMPLETION_PATH_SLUG}/lessons/{slug}").json()
        assert segment["assessment_unlocked"] is False
        assert segment["assessment_outstanding_lesson"] == outstanding_title


def test_segment_reports_unlocked_for_an_admin_regardless_of_watch_progress(completion_path_course):
    # Feature 011/016's admin exception (tests/test_watch.py::
    # test_admin_can_start_an_attempt_without_watching) bypasses the watch
    # gate entirely, so telling an admin the assessment is "unlocked" here
    # is accurate, not a fib - this is the decision current-feature.md asked
    # to be made explicit and encoded.
    lesson_slugs = completion_path_course
    _register_and_login(COMPLETION_PATH_ADMIN_EMAIL, is_admin=True)

    segment = client.get(f"/api/v1/courses/{COMPLETION_PATH_SLUG}/lessons/{lesson_slugs[1]}").json()
    assert segment["assessment_unlocked"] is True
    assert segment["assessment_outstanding_lesson"] is None
