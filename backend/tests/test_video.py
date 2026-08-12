import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db import SessionLocal
from app.main import app
from app.models.course import Course
from app.models.lesson import Lesson
from app.services import storage

client = TestClient(app)

COURSE_SLUG = "test-course-video"
WITH_VIDEO_SLUG = "test-lesson-with-video"
WITHOUT_VIDEO_SLUG = "test-lesson-without-video"


@pytest.fixture(autouse=True)
def seed_test_course():
    db = SessionLocal()
    course = Course(slug=COURSE_SLUG, title="Course For Video", description="d", is_published=True)
    db.add(course)
    db.flush()
    db.add(
        Lesson(
            course_id=course.id,
            position=1,
            slug=WITH_VIDEO_SLUG,
            title="Lesson With Video",
            description="Used to test the video-url endpoint.",
            duration_seconds=300,
            is_published=True,
            video_key="lessons/test-lesson-with-video.mp4",
        )
    )
    db.add(
        Lesson(
            course_id=course.id,
            position=2,
            slug=WITHOUT_VIDEO_SLUG,
            title="Lesson Without Video",
            description="Used to test the no-video-yet case.",
            duration_seconds=300,
            is_published=True,
            video_key=None,
        )
    )
    db.commit()
    db.close()

    yield

    db = SessionLocal()
    db.execute(delete(Course).where(Course.slug == COURSE_SLUG))
    db.commit()
    db.close()


def test_video_url_404_when_no_video():
    response = client.get(f"/api/v1/courses/{COURSE_SLUG}/lessons/{WITHOUT_VIDEO_SLUG}/video-url")
    assert response.status_code == 404
    assert response.json()["detail"] == "This lesson has no video yet"


def test_video_url_200_when_video_set(monkeypatch):
    monkeypatch.setattr(
        storage, "generate_presigned_get", lambda key, expires_in=3600: "https://example.com/signed"
    )
    response = client.get(f"/api/v1/courses/{COURSE_SLUG}/lessons/{WITH_VIDEO_SLUG}/video-url")
    assert response.status_code == 200
    body = response.json()
    assert body["url"] == "https://example.com/signed"
    assert body["expires_in"] == 3600


# Upload auth (401/403/200) is covered in test_admin_auth.py now that the
# route is guarded by require_admin instead of a shared secret header.
