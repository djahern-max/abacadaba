import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db import SessionLocal
from app.main import app
from app.models.lesson import Lesson

client = TestClient(app)

PUBLISHED_SLUG = "test-published-lesson"
UNPUBLISHED_SLUG = "test-unpublished-lesson"


@pytest.fixture(autouse=True)
def seed_test_lessons():
    db = SessionLocal()
    db.add(
        Lesson(
            slug=PUBLISHED_SLUG,
            title="Published Test Lesson",
            description="A lesson used for testing the lessons endpoints.",
            duration_seconds=300,
            is_published=True,
        )
    )
    db.add(
        Lesson(
            slug=UNPUBLISHED_SLUG,
            title="Unpublished Test Lesson",
            description="A lesson that should never appear in the public API.",
            duration_seconds=300,
            is_published=False,
        )
    )
    db.commit()
    db.close()

    yield

    db = SessionLocal()
    db.execute(delete(Lesson).where(Lesson.slug.in_([PUBLISHED_SLUG, UNPUBLISHED_SLUG])))
    db.commit()
    db.close()


def test_list_lessons_returns_list():
    response = client.get("/api/v1/lessons")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_unpublished_lesson_not_in_list():
    response = client.get("/api/v1/lessons")
    slugs = [lesson["slug"] for lesson in response.json()]
    assert PUBLISHED_SLUG in slugs
    assert UNPUBLISHED_SLUG not in slugs


def test_get_lesson_by_slug():
    response = client.get(f"/api/v1/lessons/{PUBLISHED_SLUG}")
    assert response.status_code == 200
    assert response.json()["slug"] == PUBLISHED_SLUG


def test_unknown_slug_returns_404():
    response = client.get("/api/v1/lessons/does-not-exist")
    assert response.status_code == 404
