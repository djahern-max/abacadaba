import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db import SessionLocal
from app.main import app
from app.models.attempt import Attempt
from app.models.choice import Choice
from app.models.lesson import Lesson
from app.models.question import Question
from app.models.session import Session as SessionModel
from app.models.user import User

client = TestClient(app)

SLUG_PREFIX = "test-retake-policy"
ADMIN_EMAIL = "retake-admin@example.com"
PASSWORD = "correct-horse-battery"


@pytest.fixture(autouse=True)
def cleanup():
    client.cookies.clear()

    yield

    client.cookies.clear()
    db = SessionLocal()
    lesson_ids = select(Lesson.id).where(Lesson.slug.like(f"{SLUG_PREFIX}%"))
    db.execute(delete(Attempt).where(Attempt.lesson_id.in_(lesson_ids)))
    db.execute(delete(Lesson).where(Lesson.slug.like(f"{SLUG_PREFIX}%")))
    user_ids = select(User.id).where(User.email == ADMIN_EMAIL)
    db.execute(delete(SessionModel).where(SessionModel.user_id.in_(user_ids)))
    db.execute(delete(User).where(User.email == ADMIN_EMAIL))
    db.commit()
    db.close()


def create_lesson(slug_suffix, **overrides):
    db = SessionLocal()
    lesson = Lesson(
        slug=f"{SLUG_PREFIX}-{slug_suffix}",
        title=f"Retake Policy {slug_suffix}",
        description="Used to test the retake policy.",
        duration_seconds=300,
        is_published=True,
        required_watch_ratio=0,  # ungated: these tests cover the retake policy, not watch gating
        **overrides,
    )
    db.add(lesson)
    db.flush()

    for position in range(1, 6):
        question = Question(lesson_id=lesson.id, prompt=f"Question {position}?", position=position)
        question.choices = [
            Choice(text=f"Choice {letter}", is_correct=(letter == "B"), position=index)
            for index, letter in enumerate(["A", "B", "C", "D"], start=1)
        ]
        db.add(question)

    db.commit()
    db.refresh(lesson)
    slug, lesson_id = lesson.slug, lesson.id
    db.close()
    return slug, lesson_id


def add_completed_attempt(lesson_id, completed_at, viewer_id=None, user_id=None):
    db = SessionLocal()
    db.add(
        Attempt(
            lesson_id=lesson_id,
            viewer_id=viewer_id,
            user_id=user_id,
            score=4,
            passed=True,
            completed_at=completed_at,
        )
    )
    db.commit()
    db.close()


def get_viewer_id():
    response = client.get("/api/v1/lessons")
    assert response.status_code == 200
    cookie = client.cookies.get("viewer_id")
    assert cookie is not None
    return uuid.UUID(cookie)


def start_attempt(slug):
    return client.post(f"/api/v1/lessons/{slug}/attempts")


def test_retake_inside_cooldown_returns_429_with_retry_time():
    slug, lesson_id = create_lesson("cooldown", retake_cooldown_minutes=30)
    viewer_id = get_viewer_id()
    add_completed_attempt(lesson_id, datetime.now(timezone.utc) - timedelta(minutes=5), viewer_id=viewer_id)

    response = start_attempt(slug)
    assert response.status_code == 429
    assert "after" in response.json()["detail"].lower()


def test_retake_after_cooldown_elapses_succeeds():
    slug, lesson_id = create_lesson("cooldown-elapsed", retake_cooldown_minutes=10)
    viewer_id = get_viewer_id()
    add_completed_attempt(lesson_id, datetime.now(timezone.utc) - timedelta(minutes=15), viewer_id=viewer_id)

    response = start_attempt(slug)
    assert response.status_code == 201


def test_exceeding_max_attempts_returns_429():
    slug, lesson_id = create_lesson("max-attempts", max_attempts=2)
    viewer_id = get_viewer_id()
    now = datetime.now(timezone.utc)
    add_completed_attempt(lesson_id, now - timedelta(days=2), viewer_id=viewer_id)
    add_completed_attempt(lesson_id, now - timedelta(days=1), viewer_id=viewer_id)

    response = start_attempt(slug)
    assert response.status_code == 429
    assert "attempt" in response.json()["detail"].lower()


def test_null_max_attempts_allows_many_attempts():
    slug, lesson_id = create_lesson("unlimited")
    viewer_id = get_viewer_id()
    now = datetime.now(timezone.utc)
    for i in range(10):
        add_completed_attempt(lesson_id, now - timedelta(days=i + 1), viewer_id=viewer_id)

    response = start_attempt(slug)
    assert response.status_code == 201


def test_admin_bypasses_both_limits():
    client.post(
        "/api/v1/auth/register",
        json={"email": ADMIN_EMAIL, "password": PASSWORD, "display_name": "Retake Admin"},
    )
    db = SessionLocal()
    user = db.execute(select(User).where(User.email == ADMIN_EMAIL)).scalar_one()
    user.is_admin = True
    db.commit()
    user_id = user.id
    db.close()

    slug, lesson_id = create_lesson("admin-bypass", retake_cooldown_minutes=60, max_attempts=1)
    add_completed_attempt(lesson_id, datetime.now(timezone.utc) - timedelta(minutes=1), user_id=user_id)

    response = start_attempt(slug)
    assert response.status_code == 201
