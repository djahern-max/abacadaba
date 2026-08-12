import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db import SessionLocal
from app.main import app
from app.models.course import Course
from app.models.lesson import Lesson
from app.services import storage

client = TestClient(app)

COURSE_SLUG = "test-course-thumbnail"
WITH_THUMBNAIL_SLUG = "test-lesson-with-thumbnail"
WITHOUT_THUMBNAIL_SLUG = "test-lesson-without-thumbnail"


@pytest.fixture(autouse=True)
def seed_test_course():
    db = SessionLocal()
    course = Course(
        slug=COURSE_SLUG, title="Course For Thumbnail", description="d", is_published=True, thumbnail_key="courses/test-course-thumbnail-thumb.jpg"
    )
    db.add(course)
    db.flush()
    db.add(
        Lesson(
            course_id=course.id,
            position=1,
            slug=WITH_THUMBNAIL_SLUG,
            title="Lesson With Thumbnail",
            description="Used to test the thumbnail-url endpoint.",
            duration_seconds=300,
            is_published=True,
            thumbnail_key="lessons/test-lesson-with-thumbnail-thumb.jpg",
        )
    )
    db.add(
        Lesson(
            course_id=course.id,
            position=2,
            slug=WITHOUT_THUMBNAIL_SLUG,
            title="Lesson Without Thumbnail",
            description="Used to test the no-thumbnail-yet case.",
            duration_seconds=300,
            is_published=True,
            thumbnail_key=None,
        )
    )
    db.commit()
    db.close()

    yield

    db = SessionLocal()
    db.execute(delete(Course).where(Course.slug == COURSE_SLUG))
    db.commit()
    db.close()


def test_lesson_thumbnail_url_404_when_no_thumbnail():
    response = client.get(f"/api/v1/courses/{COURSE_SLUG}/lessons/{WITHOUT_THUMBNAIL_SLUG}/thumbnail-url")
    assert response.status_code == 404
    assert response.json()["detail"] == "This lesson has no thumbnail yet"


def test_lesson_thumbnail_url_200_when_thumbnail_set(monkeypatch):
    monkeypatch.setattr(
        storage, "generate_presigned_get", lambda key, expires_in=3600: "https://example.com/signed"
    )
    response = client.get(f"/api/v1/courses/{COURSE_SLUG}/lessons/{WITH_THUMBNAIL_SLUG}/thumbnail-url")
    assert response.status_code == 200
    body = response.json()
    assert body["url"] == "https://example.com/signed"
    assert body["expires_in"] == 3600


def test_course_thumbnail_url_200_when_thumbnail_set(monkeypatch):
    monkeypatch.setattr(
        storage, "generate_presigned_get", lambda key, expires_in=3600: "https://example.com/signed"
    )
    response = client.get(f"/api/v1/courses/{COURSE_SLUG}/thumbnail-url")
    assert response.status_code == 200
    assert response.json()["url"] == "https://example.com/signed"


# Upload auth (401/403/200), size cap, and content-type rejection are
# covered in test_admin_auth.py, alongside the equivalent video tests.
