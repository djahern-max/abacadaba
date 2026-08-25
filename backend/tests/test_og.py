import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.models.course import Course
from app.services import storage

client = TestClient(app)

PUBLISHED_SLUG = "test-preview-published"
UNTHUMBNAILED_SLUG = "test-preview-no-thumbnail"
UNPUBLISHED_SLUG = "test-preview-unpublished"
LONG_DESCRIPTION = "This is a very long hook-first course description. " * 6


@pytest.fixture(autouse=True)
def seed_test_courses():
    db = SessionLocal()
    db.add(
        Course(
            slug=PUBLISHED_SLUG,
            title="Ratios in the Real World",
            description=LONG_DESCRIPTION,
            is_published=True,
            thumbnail_key="courses/test-preview-published-thumb.jpg",
        )
    )
    db.add(
        Course(
            slug=UNTHUMBNAILED_SLUG,
            title="A Course Without A Thumbnail",
            description="Short description.",
            is_published=True,
            thumbnail_key=None,
        )
    )
    db.add(
        Course(
            slug=UNPUBLISHED_SLUG,
            title="Secret Draft Course, Not For The Public",
            description="This description must never leak to a crawler.",
            is_published=False,
        )
    )
    db.commit()
    db.close()

    yield

    db = SessionLocal()
    db.execute(delete(Course).where(Course.slug.in_([PUBLISHED_SLUG, UNTHUMBNAILED_SLUG, UNPUBLISHED_SLUG])))
    db.commit()
    db.close()


def test_published_course_preview_returns_course_meta(monkeypatch):
    monkeypatch.setattr(
        storage, "generate_presigned_get", lambda key, expires_in=3600: "https://spaces.example.com/signed-thumb"
    )
    response = client.get(f"/api/v1/og/courses/{PUBLISHED_SLUG}")
    assert response.status_code == 200
    body = response.text

    assert '<meta property="og:title" content="Ratios in the Real World">' in body
    assert f'<meta property="og:url" content="{settings.site_url}/courses/{PUBLISHED_SLUG}">' in body
    assert '<meta property="og:image" content="https://spaces.example.com/signed-thumb">' in body
    assert '<meta property="og:type" content="website">' in body
    assert '<meta name="twitter:card" content="summary_large_image">' in body


def test_published_course_preview_description_is_truncated(monkeypatch):
    monkeypatch.setattr(storage, "generate_presigned_get", lambda key, expires_in=3600: "https://example.com/x")
    response = client.get(f"/api/v1/og/courses/{PUBLISHED_SLUG}")
    body = response.text

    assert len(LONG_DESCRIPTION) > 200
    assert LONG_DESCRIPTION.strip() not in body
    assert "…" in body


def test_published_course_without_thumbnail_falls_back_to_default_image():
    response = client.get(f"/api/v1/og/courses/{UNTHUMBNAILED_SLUG}")
    body = response.text

    assert f'<meta property="og:image" content="{settings.site_url}/og-default.png">' in body
    assert '<meta property="og:title" content="A Course Without A Thumbnail">' in body


def test_unpublished_course_returns_site_default_and_leaks_nothing():
    response = client.get(f"/api/v1/og/courses/{UNPUBLISHED_SLUG}")
    assert response.status_code == 200
    body = response.text

    assert "Secret Draft Course" not in body
    assert "must never leak" not in body
    assert '<meta property="og:title" content="abacadaba">' in body
    assert f'<meta property="og:url" content="{settings.site_url}/">' in body


def test_unknown_slug_returns_site_default():
    response = client.get("/api/v1/og/courses/does-not-exist")
    assert response.status_code == 200
    assert '<meta property="og:title" content="abacadaba">' in response.text


def test_default_preview_has_absolute_image_url():
    response = client.get("/api/v1/og/courses/does-not-exist")
    body = response.text
    assert f'content="{settings.site_url}/og-default.png"' in body
    assert '<meta property="og:image:width" content="1200">' in body
    assert '<meta property="og:image:height" content="630">' in body
