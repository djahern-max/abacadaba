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
ALL_TEST_SLUGS = [PUBLISHED_SLUG, UNPUBLISHED_SLUG]


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
