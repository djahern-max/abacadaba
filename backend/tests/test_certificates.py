import uuid

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

QUIZ_SLUG = "test-lesson-certificates"
SIGNED_IN_EMAIL = "certificates-user@example.com"
SIGNED_IN_PASSWORD = "correct-horse-battery"
SIGNED_IN_DISPLAY_NAME = "Grace Hopper Account"


@pytest.fixture(autouse=True)
def seed_test_lesson():
    db = SessionLocal()

    lesson = Lesson(
        slug=QUIZ_SLUG,
        title="Lesson For Certificates",
        description="Used to test the certificate endpoints.",
        duration_seconds=300,
        is_published=True,
    )
    db.add(lesson)
    db.flush()

    for position in range(1, 6):
        question = Question(
            lesson_id=lesson.id,
            prompt=f"Question {position}?",
            position=position,
        )
        question.choices = [
            Choice(text=f"Choice {letter}", is_correct=(letter == "B"), position=index)
            for index, letter in enumerate(["A", "B", "C", "D"], start=1)
        ]
        db.add(question)

    db.commit()
    db.close()

    yield

    db = SessionLocal()
    lesson_ids = select(Lesson.id).where(Lesson.slug == QUIZ_SLUG)
    db.execute(delete(Attempt).where(Attempt.lesson_id.in_(lesson_ids)))
    db.execute(delete(Lesson).where(Lesson.slug == QUIZ_SLUG))
    db.commit()
    db.close()

    client.cookies.clear()

    db = SessionLocal()
    user_ids = select(User.id).where(User.email == SIGNED_IN_EMAIL)
    db.execute(delete(SessionModel).where(SessionModel.user_id.in_(user_ids)))
    db.execute(delete(User).where(User.email == SIGNED_IN_EMAIL))
    db.commit()
    db.close()


def get_questions():
    db = SessionLocal()
    stmt = (
        select(Question)
        .join(Lesson)
        .where(Lesson.slug == QUIZ_SLUG)
        .order_by(Question.position)
    )
    questions = db.execute(stmt).scalars().all()
    result = []
    for question in questions:
        correct_choice = next(c for c in question.choices if c.is_correct)
        wrong_choice = next(c for c in question.choices if not c.is_correct)
        result.append(
            {
                "question_id": question.id,
                "correct_choice_id": correct_choice.id,
                "wrong_choice_id": wrong_choice.id,
            }
        )
    db.close()
    return result


def answer(attempt_id, question_id, choice_id):
    return client.post(
        f"/api/v1/attempts/{attempt_id}/answers",
        json={"question_id": question_id, "choice_id": choice_id},
    )


def start_and_pass_attempt():
    response = client.post(f"/api/v1/lessons/{QUIZ_SLUG}/attempts")
    attempt_id = response.json()["attempt_id"]
    for q in get_questions():
        answer(attempt_id, q["question_id"], q["correct_choice_id"])
    return attempt_id


def start_and_fail_attempt():
    response = client.post(f"/api/v1/lessons/{QUIZ_SLUG}/attempts")
    attempt_id = response.json()["attempt_id"]
    questions = get_questions()
    for q in questions[:2]:
        answer(attempt_id, q["question_id"], q["correct_choice_id"])
    for q in questions[2:]:
        answer(attempt_id, q["question_id"], q["wrong_choice_id"])
    return attempt_id


def start_incomplete_attempt():
    response = client.post(f"/api/v1/lessons/{QUIZ_SLUG}/attempts")
    attempt_id = response.json()["attempt_id"]
    questions = get_questions()
    answer(attempt_id, questions[0]["question_id"], questions[0]["correct_choice_id"])
    return attempt_id


def claim(attempt_id, name="Ada Lovelace"):
    return client.post(f"/api/v1/attempts/{attempt_id}/certificate", json={"recipient_name": name})


def test_claiming_on_a_passed_attempt_returns_a_code_and_the_name():
    attempt_id = start_and_pass_attempt()
    response = claim(attempt_id, "Ada Lovelace")
    assert response.status_code == 200
    body = response.json()
    assert body["recipient_name"] == "Ada Lovelace"
    assert body["certificate_code"]
    assert body["lesson_title"] == "Lesson For Certificates"
    assert body["score"] == 5


def test_claiming_on_a_failed_attempt_returns_409():
    attempt_id = start_and_fail_attempt()
    response = claim(attempt_id)
    assert response.status_code == 409


def test_claiming_on_an_incomplete_attempt_returns_409():
    attempt_id = start_incomplete_attempt()
    response = claim(attempt_id)
    assert response.status_code == 409


def test_claiming_twice_keeps_the_original_code_and_updates_the_name():
    attempt_id = start_and_pass_attempt()
    first = claim(attempt_id, "Ada Lovelace")
    second = claim(attempt_id, "Grace Hopper")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["certificate_code"] == second.json()["certificate_code"]
    assert second.json()["recipient_name"] == "Grace Hopper"


def test_empty_or_whitespace_only_name_returns_422():
    attempt_id = start_and_pass_attempt()
    assert claim(attempt_id, "").status_code == 422
    assert claim(attempt_id, "   ").status_code == 422


def test_pdf_endpoint_returns_a_pdf():
    attempt_id = start_and_pass_attempt()
    claim(attempt_id)

    response = client.get(f"/api/v1/attempts/{attempt_id}/certificate.pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_pdf_endpoint_before_claiming_returns_409():
    attempt_id = start_and_pass_attempt()
    response = client.get(f"/api/v1/attempts/{attempt_id}/certificate.pdf")
    assert response.status_code == 409


def test_verifying_a_real_code_returns_valid_true_with_lesson_and_score():
    attempt_id = start_and_pass_attempt()
    code = claim(attempt_id).json()["certificate_code"]

    response = client.get(f"/api/v1/certificates/{code}")
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["lesson_title"] == "Lesson For Certificates"
    assert body["score"] == 5


def test_verifying_an_unknown_code_returns_200_with_valid_false():
    response = client.get("/api/v1/certificates/ZZZZ-ZZZZ-ZZZZ")
    assert response.status_code == 200
    assert response.json()["valid"] is False


def test_verifying_is_case_insensitive_and_tolerates_missing_hyphens():
    attempt_id = start_and_pass_attempt()
    code = claim(attempt_id).json()["certificate_code"]

    lowercase_response = client.get(f"/api/v1/certificates/{code.lower()}")
    assert lowercase_response.status_code == 200
    assert lowercase_response.json()["valid"] is True

    unhyphenated_response = client.get(f"/api/v1/certificates/{code.replace('-', '')}")
    assert unhyphenated_response.status_code == 200
    assert unhyphenated_response.json()["valid"] is True


def test_verifying_an_anonymous_certificate_reports_not_an_account_holder():
    attempt_id = start_and_pass_attempt()
    code = claim(attempt_id, "Ada Lovelace").json()["certificate_code"]

    response = client.get(f"/api/v1/certificates/{code}")
    assert response.json()["is_account_holder"] is False


def test_claiming_while_signed_in_uses_the_account_display_name_without_a_body_name():
    client.post(
        "/api/v1/auth/register",
        json={
            "email": SIGNED_IN_EMAIL,
            "password": SIGNED_IN_PASSWORD,
            "display_name": SIGNED_IN_DISPLAY_NAME,
        },
    )

    attempt_id = start_and_pass_attempt()
    response = client.post(f"/api/v1/attempts/{attempt_id}/certificate", json={})
    assert response.status_code == 200
    assert response.json()["recipient_name"] == SIGNED_IN_DISPLAY_NAME

    verify_response = client.get(f"/api/v1/certificates/{response.json()['certificate_code']}")
    assert verify_response.json()["is_account_holder"] is True


def test_claiming_while_signed_in_ignores_any_name_sent_in_the_body():
    client.post(
        "/api/v1/auth/register",
        json={
            "email": SIGNED_IN_EMAIL,
            "password": SIGNED_IN_PASSWORD,
            "display_name": SIGNED_IN_DISPLAY_NAME,
        },
    )

    attempt_id = start_and_pass_attempt()
    response = claim(attempt_id, "Someone Else Entirely")
    assert response.status_code == 200
    assert response.json()["recipient_name"] == SIGNED_IN_DISPLAY_NAME
