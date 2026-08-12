from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db import SessionLocal
from app.main import app
from app.models.attempt import Attempt
from app.models.choice import Choice
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.question import Question
from app.models.session import Session as SessionModel
from app.models.user import User

client = TestClient(app)

SLUG_PREFIX = "test-retake-policy"
ADMIN_EMAIL = "retake-admin@example.com"
USER_EMAIL = "retake-user@example.com"
PASSWORD = "correct-horse-battery"


@pytest.fixture(autouse=True)
def cleanup():
    client.cookies.clear()

    yield

    client.cookies.clear()
    db = SessionLocal()
    course_ids = select(Course.id).where(Course.slug.like(f"{SLUG_PREFIX}%"))
    db.execute(delete(Attempt).where(Attempt.course_id.in_(course_ids)))
    db.execute(delete(Course).where(Course.slug.like(f"{SLUG_PREFIX}%")))
    emails = [ADMIN_EMAIL, USER_EMAIL]
    user_ids = select(User.id).where(User.email.in_(emails))
    db.execute(delete(SessionModel).where(SessionModel.user_id.in_(user_ids)))
    db.execute(delete(User).where(User.email.in_(emails)))
    db.commit()
    db.close()


def create_course(slug_suffix, **overrides):
    db = SessionLocal()
    course = Course(
        slug=f"{SLUG_PREFIX}-{slug_suffix}",
        title=f"Retake Policy {slug_suffix}",
        description="Used to test the retake policy.",
        is_published=True,
        **overrides,
    )
    db.add(course)
    db.flush()

    lesson = Lesson(
        course_id=course.id,
        position=1,
        slug=f"{SLUG_PREFIX}-{slug_suffix}-lesson",
        title=f"Retake Policy Lesson {slug_suffix}",
        description="Used to test the retake policy.",
        duration_seconds=300,
        is_published=True,
        required_watch_ratio=0,  # ungated: these tests cover the retake policy, not watch gating
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
    db.refresh(course)
    slug, course_id = course.slug, course.id
    db.close()
    return slug, course_id


def add_completed_attempt(course_id, completed_at, viewer_id=None, user_id=None):
    db = SessionLocal()
    db.add(
        Attempt(
            course_id=course_id,
            viewer_id=viewer_id,
            user_id=user_id,
            score=4,
            passed=True,
            completed_at=completed_at,
        )
    )
    db.commit()
    db.close()


def register_and_login(email):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "display_name": "Retake Tester"},
    )
    db = SessionLocal()
    user_id = db.execute(select(User.id).where(User.email == email)).scalar_one()
    db.close()
    return user_id


def start_attempt(slug):
    return client.post(f"/api/v1/courses/{slug}/attempts")


def test_retake_inside_cooldown_returns_429_with_retry_time():
    slug, course_id = create_course("cooldown", retake_cooldown_minutes=30)
    user_id = register_and_login(USER_EMAIL)
    add_completed_attempt(course_id, datetime.now(timezone.utc) - timedelta(minutes=5), user_id=user_id)

    response = start_attempt(slug)
    assert response.status_code == 429
    assert "after" in response.json()["detail"].lower()


def test_retake_after_cooldown_elapses_succeeds():
    slug, course_id = create_course("cooldown-elapsed", retake_cooldown_minutes=10)
    user_id = register_and_login(USER_EMAIL)
    add_completed_attempt(course_id, datetime.now(timezone.utc) - timedelta(minutes=15), user_id=user_id)

    response = start_attempt(slug)
    assert response.status_code == 201


def test_exceeding_max_attempts_returns_429():
    slug, course_id = create_course("max-attempts", max_attempts=2)
    user_id = register_and_login(USER_EMAIL)
    now = datetime.now(timezone.utc)
    add_completed_attempt(course_id, now - timedelta(days=2), user_id=user_id)
    add_completed_attempt(course_id, now - timedelta(days=1), user_id=user_id)

    response = start_attempt(slug)
    assert response.status_code == 429
    assert "attempt" in response.json()["detail"].lower()


def test_null_max_attempts_allows_many_attempts():
    slug, course_id = create_course("unlimited")
    user_id = register_and_login(USER_EMAIL)
    now = datetime.now(timezone.utc)
    for i in range(10):
        add_completed_attempt(course_id, now - timedelta(days=i + 1), user_id=user_id)

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

    slug, course_id = create_course("admin-bypass", retake_cooldown_minutes=60, max_attempts=1)
    add_completed_attempt(course_id, datetime.now(timezone.utc) - timedelta(minutes=1), user_id=user_id)

    response = start_attempt(slug)
    assert response.status_code == 201
