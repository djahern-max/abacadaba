import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import delete, select

from app.db import SessionLocal
from app.main import app
from app.models.lesson import Lesson
from app.models.session import Session as SessionModel
from app.models.user import User
from app.services import storage

client = TestClient(app)

LESSON_SLUG = "test-lesson-admin-auth"
ADMIN_EMAIL = "admin@example.com"
MEMBER_EMAIL = "member@example.com"
PASSWORD = "correct-horse-battery"


def make_jpeg_bytes(size=(1280, 720)):
    buffer = io.BytesIO()
    Image.new("RGB", size, color=(120, 60, 200)).save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def seed_lesson_and_users():
    client.cookies.clear()

    db = SessionLocal()
    db.add(
        Lesson(
            slug=LESSON_SLUG,
            title="Lesson For Admin Auth",
            description="Used to test the upload guard.",
            duration_seconds=300,
            is_published=True,
        )
    )
    db.commit()
    db.close()

    yield

    client.cookies.clear()

    db = SessionLocal()
    emails = [ADMIN_EMAIL, MEMBER_EMAIL]
    user_ids = select(User.id).where(User.email.in_(emails))
    db.execute(delete(SessionModel).where(SessionModel.user_id.in_(user_ids)))
    db.execute(delete(User).where(User.email.in_(emails)))
    db.execute(delete(Lesson).where(Lesson.slug == LESSON_SLUG))
    db.commit()
    db.close()


def register_and_login(email, is_admin=False):
    # Registering already sets the session cookie; promoting to admin
    # afterward doesn't touch that session, so it's still valid to reuse.
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "display_name": "Test User"},
    )
    if is_admin:
        db = SessionLocal()
        user = db.execute(select(User).where(User.email == email)).scalar_one()
        user.is_admin = True
        db.commit()
        db.close()


def upload(**kwargs):
    return client.post(
        f"/api/v1/admin/lessons/{LESSON_SLUG}/video",
        files={"file": ("video.mp4", io.BytesIO(b"data"), "video/mp4")},
        **kwargs,
    )


def test_upload_with_no_session_returns_401():
    response = upload()
    assert response.status_code == 401


def test_upload_as_a_non_admin_returns_403():
    register_and_login(MEMBER_EMAIL, is_admin=False)

    response = upload()
    assert response.status_code == 403


def test_upload_as_an_admin_succeeds(monkeypatch):
    monkeypatch.setattr(storage, "upload_fileobj", lambda fileobj, key, content_type: None)
    register_and_login(ADMIN_EMAIL, is_admin=True)

    response = upload()
    assert response.status_code == 200
    assert response.json()["video_key"] == f"lessons/{LESSON_SLUG}.mp4"


def get_lesson_id():
    db = SessionLocal()
    lesson = db.execute(select(Lesson).where(Lesson.slug == LESSON_SLUG)).scalar_one()
    lesson_id = lesson.id
    db.close()
    return lesson_id


def upload_thumbnail(content=None, content_type="image/jpeg", filename="thumb.jpg", **kwargs):
    if content is None:
        content = make_jpeg_bytes()
    return client.post(
        f"/api/v1/admin/lessons/{get_lesson_id()}/thumbnail",
        files={"file": (filename, io.BytesIO(content), content_type)},
        **kwargs,
    )


def test_thumbnail_upload_with_no_session_returns_401():
    response = upload_thumbnail()
    assert response.status_code == 401


def test_thumbnail_upload_as_a_non_admin_returns_403():
    register_and_login(MEMBER_EMAIL, is_admin=False)

    response = upload_thumbnail()
    assert response.status_code == 403


def test_thumbnail_upload_as_an_admin_succeeds(monkeypatch):
    monkeypatch.setattr(storage, "upload_fileobj", lambda fileobj, key, content_type: None)
    register_and_login(ADMIN_EMAIL, is_admin=True)

    response = upload_thumbnail()
    assert response.status_code == 200
    assert response.json()["thumbnail_key"] == f"lessons/{LESSON_SLUG}-thumb.jpg"


def test_thumbnail_upload_oversized_file_is_rejected():
    register_and_login(ADMIN_EMAIL, is_admin=True)

    oversized = b"x" * (2 * 1024 * 1024 + 1)
    response = upload_thumbnail(content=oversized)
    assert response.status_code == 400


def test_thumbnail_upload_wrong_content_type_is_rejected():
    register_and_login(ADMIN_EMAIL, is_admin=True)

    response = upload_thumbnail(content_type="application/pdf", filename="thumb.pdf")
    assert response.status_code == 400


def test_thumbnail_upload_pdf_renamed_to_jpg_is_rejected():
    register_and_login(ADMIN_EMAIL, is_admin=True)

    response = upload_thumbnail(content=b"%PDF-1.4 not actually an image", content_type="image/jpeg")
    assert response.status_code == 400
