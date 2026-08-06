import io
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db import SessionLocal
from app.main import app
from app.models.attempt import Attempt
from app.models.attempt_answer import AttemptAnswer
from app.models.choice import Choice
from app.models.lesson import Lesson
from app.models.question import Question
from app.models.session import Session as SessionModel
from app.models.user import User
from app.services import storage

client = TestClient(app)

SLUG_PREFIX = "test-admin-content"
ADMIN_EMAIL = "admin-content@example.com"
MEMBER_EMAIL = "member-content@example.com"
PASSWORD = "correct-horse-battery"

ADMIN_ROUTES = [
    ("GET", "/api/v1/admin/lessons"),
    ("POST", "/api/v1/admin/lessons"),
    ("GET", "/api/v1/admin/lessons/999999"),
    ("PATCH", "/api/v1/admin/lessons/999999"),
    ("DELETE", "/api/v1/admin/lessons/999999"),
    ("POST", "/api/v1/admin/lessons/999999/publish"),
    ("POST", "/api/v1/admin/lessons/999999/unpublish"),
    ("POST", "/api/v1/admin/lessons/999999/questions"),
    ("PATCH", "/api/v1/admin/questions/999999"),
    ("DELETE", "/api/v1/admin/questions/999999"),
    ("POST", "/api/v1/admin/questions/999999/move"),
    ("POST", "/api/v1/admin/questions/999999/choices"),
    ("PATCH", "/api/v1/admin/choices/999999"),
    ("DELETE", "/api/v1/admin/choices/999999"),
    ("POST", "/api/v1/admin/choices/999999/move"),
    ("POST", "/api/v1/admin/questions/999999/correct-choice"),
]


@pytest.fixture(autouse=True)
def cleanup():
    client.cookies.clear()

    yield

    client.cookies.clear()
    db = SessionLocal()
    emails = [ADMIN_EMAIL, MEMBER_EMAIL]
    user_ids = select(User.id).where(User.email.in_(emails))
    lesson_ids = select(Lesson.id).where(Lesson.slug.like(f"{SLUG_PREFIX}%"))
    question_ids = select(Question.id).where(Question.lesson_id.in_(lesson_ids))
    attempt_ids = select(Attempt.id).where(Attempt.lesson_id.in_(lesson_ids))
    db.execute(delete(AttemptAnswer).where(AttemptAnswer.attempt_id.in_(attempt_ids)))
    db.execute(delete(Attempt).where(Attempt.lesson_id.in_(lesson_ids)))
    db.execute(delete(Choice).where(Choice.question_id.in_(question_ids)))
    db.execute(delete(Question).where(Question.lesson_id.in_(lesson_ids)))
    db.execute(delete(Lesson).where(Lesson.slug.like(f"{SLUG_PREFIX}%")))
    db.execute(delete(SessionModel).where(SessionModel.user_id.in_(user_ids)))
    db.execute(delete(User).where(User.email.in_(emails)))
    db.commit()
    db.close()


def register_and_login(email, is_admin=False):
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


def login_admin():
    register_and_login(ADMIN_EMAIL, is_admin=True)


def create_lesson(slug_suffix, **overrides):
    payload = {"title": f"Admin Test Lesson {slug_suffix}", "slug": f"{SLUG_PREFIX}-{slug_suffix}"}
    payload.update(overrides)
    response = client.post("/api/v1/admin/lessons", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def add_complete_questions(lesson_id, count=5):
    for i in range(count):
        question = client.post(
            f"/api/v1/admin/lessons/{lesson_id}/questions", json={"prompt": f"Question {i}"}
        )
        assert question.status_code == 201, question.text
        question_id = question.json()["id"]
        for j in range(4):
            choice = client.post(
                f"/api/v1/admin/questions/{question_id}/choices",
                json={"text": f"Choice {j}", "is_correct": j == 0},
            )
            assert choice.status_code == 201, choice.text


@pytest.mark.parametrize("method,path", ADMIN_ROUTES)
def test_anonymous_gets_401(method, path):
    response = client.request(method, path, json={})
    assert response.status_code == 401


@pytest.mark.parametrize("method,path", ADMIN_ROUTES)
def test_non_admin_gets_403(method, path):
    register_and_login(MEMBER_EMAIL, is_admin=False)
    response = client.request(method, path, json={})
    assert response.status_code == 403


def test_create_lesson_is_unpublished():
    login_admin()
    lesson = create_lesson("create")
    assert lesson["is_published"] is False
    assert lesson["questions"] == []


def test_publish_with_four_questions_returns_422():
    login_admin()
    lesson = create_lesson("four-questions")
    add_complete_questions(lesson["id"], count=4)

    response = client.post(f"/api/v1/admin/lessons/{lesson['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("must have exactly 5 questions" in error for error in errors)


def test_publish_with_missing_correct_choice_returns_422():
    login_admin()
    lesson = create_lesson("no-correct-choice")
    add_complete_questions(lesson["id"], count=5)

    detail = client.get(f"/api/v1/admin/lessons/{lesson['id']}").json()
    first_choice_id = detail["questions"][0]["choices"][0]["id"]
    unset = client.patch(f"/api/v1/admin/choices/{first_choice_id}", json={"is_correct": False})
    assert unset.status_code == 200

    response = client.post(f"/api/v1/admin/lessons/{lesson['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("must have exactly one correct choice" in error for error in errors)


def test_publish_complete_lesson_succeeds_and_appears_in_public_list(monkeypatch):
    monkeypatch.setattr(storage, "upload_fileobj", lambda fileobj, key, content_type: None)
    login_admin()
    lesson = create_lesson("complete", description="A complete test lesson.")
    add_complete_questions(lesson["id"], count=5)
    upload = client.post(
        f"/api/v1/admin/lessons/{lesson['slug']}/video",
        files={"file": ("video.mp4", io.BytesIO(b"data"), "video/mp4")},
    )
    assert upload.status_code == 200

    response = client.post(f"/api/v1/admin/lessons/{lesson['id']}/publish")
    assert response.status_code == 200
    assert response.json()["is_published"] is True

    public = client.get("/api/v1/lessons")
    assert lesson["slug"] in [item["slug"] for item in public.json()]


def test_unpublish_removes_from_public_list(monkeypatch):
    monkeypatch.setattr(storage, "upload_fileobj", lambda fileobj, key, content_type: None)
    login_admin()
    lesson = create_lesson("unpublish", description="A lesson to unpublish.")
    add_complete_questions(lesson["id"], count=5)
    client.post(
        f"/api/v1/admin/lessons/{lesson['slug']}/video",
        files={"file": ("video.mp4", io.BytesIO(b"data"), "video/mp4")},
    )
    client.post(f"/api/v1/admin/lessons/{lesson['id']}/publish")

    response = client.post(f"/api/v1/admin/lessons/{lesson['id']}/unpublish")
    assert response.status_code == 200
    assert response.json()["is_published"] is False

    public = client.get("/api/v1/lessons")
    assert lesson["slug"] not in [item["slug"] for item in public.json()]


def test_setting_correct_choice_clears_previous():
    login_admin()
    lesson = create_lesson("correct-swap")
    question = client.post(
        f"/api/v1/admin/lessons/{lesson['id']}/questions", json={"prompt": "Which one?"}
    ).json()
    choice_a = client.post(
        f"/api/v1/admin/questions/{question['id']}/choices", json={"text": "A", "is_correct": True}
    ).json()
    choice_b = client.post(
        f"/api/v1/admin/questions/{question['id']}/choices", json={"text": "B"}
    ).json()

    response = client.post(
        f"/api/v1/admin/questions/{question['id']}/correct-choice", json={"choice_id": choice_b["id"]}
    )
    assert response.status_code == 204

    detail = client.get(f"/api/v1/admin/lessons/{lesson['id']}").json()
    choices = detail["questions"][0]["choices"]
    correct_ids = [choice["id"] for choice in choices if choice["is_correct"]]
    assert correct_ids == [choice_b["id"]]


def test_reordering_questions_produces_contiguous_positions():
    login_admin()
    lesson = create_lesson("reorder")
    q1 = client.post(f"/api/v1/admin/lessons/{lesson['id']}/questions", json={"prompt": "Q1"}).json()
    q2 = client.post(f"/api/v1/admin/lessons/{lesson['id']}/questions", json={"prompt": "Q2"}).json()
    q3 = client.post(f"/api/v1/admin/lessons/{lesson['id']}/questions", json={"prompt": "Q3"}).json()

    # Q1, Q2, Q3 -> move Q3 up -> Q1, Q3, Q2 -> move Q3 up again -> Q3, Q1, Q2
    assert client.post(f"/api/v1/admin/questions/{q3['id']}/move", json={"direction": "up"}).status_code == 204
    assert client.post(f"/api/v1/admin/questions/{q3['id']}/move", json={"direction": "up"}).status_code == 204

    detail = client.get(f"/api/v1/admin/lessons/{lesson['id']}").json()
    positions = [(question["id"], question["position"]) for question in detail["questions"]]
    assert [position for _, position in positions] == [1, 2, 3]
    assert [question_id for question_id, _ in positions] == [q3["id"], q1["id"], q2["id"]]


def test_delete_lesson_with_completed_attempt_returns_409():
    login_admin()
    lesson = create_lesson("delete-with-attempt")

    db = SessionLocal()
    db.add(
        Attempt(
            lesson_id=lesson["id"], score=4, passed=True, completed_at=datetime.now(timezone.utc)
        )
    )
    db.commit()
    db.close()

    response = client.delete(f"/api/v1/admin/lessons/{lesson['id']}")
    assert response.status_code == 409
