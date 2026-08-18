import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db import SessionLocal
from app.main import app
from app.models.course import Course
from app.models.lesson import Lesson

client = TestClient(app)

PUBLISHED_SLUG = "test-published-course"
UNPUBLISHED_SLUG = "test-unpublished-course"
SINGLE_LESSON_SLUG = "test-single-lesson-course"
ALL_TEST_SLUGS = [PUBLISHED_SLUG, UNPUBLISHED_SLUG, SINGLE_LESSON_SLUG]


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
