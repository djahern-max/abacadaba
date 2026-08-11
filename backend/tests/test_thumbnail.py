import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db import SessionLocal
from app.main import app
from app.models.lesson import Lesson
from app.services import storage

client = TestClient(app)

WITH_THUMBNAIL_SLUG = "test-lesson-with-thumbnail"
WITHOUT_THUMBNAIL_SLUG = "test-lesson-without-thumbnail"


@pytest.fixture(autouse=True)
def seed_test_lessons():
    db = SessionLocal()
    db.add(
        Lesson(
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
    db.execute(delete(Lesson).where(Lesson.slug.in_([WITH_THUMBNAIL_SLUG, WITHOUT_THUMBNAIL_SLUG])))
    db.commit()
    db.close()


def test_thumbnail_url_404_when_no_thumbnail(monkeypatch):
    response = client.get(f"/api/v1/lessons/{WITHOUT_THUMBNAIL_SLUG}/thumbnail-url")
    assert response.status_code == 404
    assert response.json()["detail"] == "This lesson has no thumbnail yet"


def test_thumbnail_url_200_when_thumbnail_set(monkeypatch):
    monkeypatch.setattr(
        storage, "generate_presigned_get", lambda key, expires_in=3600: "https://example.com/signed"
    )
    response = client.get(f"/api/v1/lessons/{WITH_THUMBNAIL_SLUG}/thumbnail-url")
    assert response.status_code == 200
    body = response.json()
    assert body["url"] == "https://example.com/signed"
    assert body["expires_in"] == 3600


# Upload auth (401/403/200), size cap, and content-type rejection are
# covered in test_admin_auth.py, alongside the equivalent video tests.
