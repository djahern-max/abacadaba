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

client = TestClient(app)

LESSON_SLUG = "test-lesson-analytics"
ADMIN_EMAIL = "analytics-admin@example.com"
PASSWORD = "correct-horse-battery"

# Answer matrix: each completed attempt (a, b, c) answers all five questions;
# attempt d drops off after question 2; attempt e never answers anything.
# Question 4 is answered wrong by everyone (0% correct, the "everyone gets it
# wrong" case); question 1 is answered correctly by everyone (100%).
ATTEMPTS = {
    "a": {"answers": {1: "B", 2: "B", 3: "B", 4: "C", 5: "B"}, "completed": True, "score": 4, "passed": True},
    "b": {"answers": {1: "B", 2: "B", 3: "C", 4: "C", 5: "B"}, "completed": True, "score": 3, "passed": False},
    "c": {"answers": {1: "B", 2: "C", 3: "C", 4: "C", 5: "B"}, "completed": True, "score": 2, "passed": False},
    "d": {"answers": {1: "B", 2: "C"}, "completed": False, "score": None, "passed": None},
    "e": {"answers": {}, "completed": False, "score": None, "passed": None},
}
LETTER_TO_POSITION = {"A": 1, "B": 2, "C": 3, "D": 4}


@pytest.fixture(autouse=True)
def seed_data():
    client.cookies.clear()
    db = SessionLocal()

    lesson = Lesson(
        slug=LESSON_SLUG,
        title="Lesson For Analytics",
        description="Used to test analytics.",
        duration_seconds=300,
        is_published=True,
    )
    db.add(lesson)
    db.flush()

    questions = []
    for position in range(1, 6):
        question = Question(lesson_id=lesson.id, prompt=f"Question {position}?", position=position)
        question.choices = [
            Choice(text=f"Choice {letter}", is_correct=(letter == "B"), position=index)
            for letter, index in LETTER_TO_POSITION.items()
        ]
        db.add(question)
        questions.append(question)
    db.flush()

    choices_by_question_position = {q.position: {c.position: c for c in q.choices} for q in questions}
    questions_by_position = {q.position: q for q in questions}

    for spec in ATTEMPTS.values():
        attempt = Attempt(
            lesson_id=lesson.id,
            completed_at=datetime.now(timezone.utc) if spec["completed"] else None,
            score=spec["score"],
            passed=spec["passed"],
        )
        db.add(attempt)
        db.flush()
        for question_position, letter in spec["answers"].items():
            picked = choices_by_question_position[question_position][LETTER_TO_POSITION[letter]]
            db.add(
                AttemptAnswer(
                    attempt_id=attempt.id,
                    question_id=questions_by_position[question_position].id,
                    choice_id=picked.id,
                    is_correct=picked.is_correct,
                )
            )
        db.flush()

    db.commit()
    db.close()

    yield

    db = SessionLocal()
    lesson_ids = select(Lesson.id).where(Lesson.slug == LESSON_SLUG)
    attempt_ids = select(Attempt.id).where(Attempt.lesson_id.in_(lesson_ids))
    db.execute(delete(AttemptAnswer).where(AttemptAnswer.attempt_id.in_(attempt_ids)))
    db.execute(delete(Attempt).where(Attempt.lesson_id.in_(lesson_ids)))
    db.execute(delete(Lesson).where(Lesson.slug == LESSON_SLUG))
    user_ids = select(User.id).where(User.email == ADMIN_EMAIL)
    db.execute(delete(SessionModel).where(SessionModel.user_id.in_(user_ids)))
    db.execute(delete(User).where(User.email == ADMIN_EMAIL))
    db.commit()
    db.close()
    client.cookies.clear()


def login_admin():
    client.post(
        "/api/v1/auth/register",
        json={"email": ADMIN_EMAIL, "password": PASSWORD, "display_name": "Analytics Admin"},
    )
    db = SessionLocal()
    user = db.execute(select(User).where(User.email == ADMIN_EMAIL)).scalar_one()
    user.is_admin = True
    db.commit()
    db.close()


def get_lesson_id():
    db = SessionLocal()
    lesson_id = db.execute(select(Lesson.id).where(Lesson.slug == LESSON_SLUG)).scalar_one()
    db.close()
    return lesson_id


def get_stats():
    login_admin()
    response = client.get(f"/api/v1/admin/lessons/{get_lesson_id()}/stats")
    assert response.status_code == 200, response.text
    return response.json()


def test_lesson_stats_are_arithmetically_correct():
    stats = get_stats()["lesson_stats"]
    assert stats["attempts_started"] == 5
    assert stats["attempts_completed"] == 3
    assert stats["completion_rate"] == pytest.approx(0.6)
    assert stats["pass_rate"] == pytest.approx(1 / 3)
    assert stats["mean_score"] == pytest.approx(3.0)


def test_question_stats_put_the_worst_question_first_and_it_is_flaggable():
    questions = get_stats()["question_stats"]

    # Question 4: everyone got it wrong. It must sort first and read 0%,
    # which the frontend flags as a likely bad question (< 40%).
    assert questions[0]["position"] == 4
    assert questions[0]["pct_correct"] == pytest.approx(0.0)
    assert questions[0]["answered"] == 3

    assert questions[1]["position"] == 3
    assert questions[1]["pct_correct"] == pytest.approx(100 / 3)
    assert questions[1]["answered"] == 3

    by_position = {q["position"]: q for q in questions}
    assert by_position[2]["pct_correct"] == pytest.approx(50.0)
    assert by_position[2]["answered"] == 4
    assert by_position[1]["pct_correct"] == pytest.approx(100.0)
    assert by_position[1]["answered"] == 4
    assert by_position[5]["pct_correct"] == pytest.approx(100.0)
    assert by_position[5]["answered"] == 3


def test_choice_distribution_counts_picks_and_flags_the_correct_choice():
    body = get_stats()
    question_id_by_position = {q["position"]: q["question_id"] for q in body["question_stats"]}
    distribution_by_question_id = {row["question_id"]: row["choices"] for row in body["choice_distribution"]}

    q4_choices = {c["text"][-1]: c for c in distribution_by_question_id[question_id_by_position[4]]}
    assert q4_choices["C"]["picked_count"] == 3
    assert q4_choices["B"]["picked_count"] == 0
    assert q4_choices["B"]["is_correct"] is True
    assert q4_choices["C"]["is_correct"] is False

    q1_choices = {c["text"][-1]: c for c in distribution_by_question_id[question_id_by_position[1]]}
    assert q1_choices["B"]["picked_count"] == 4


def test_dropoff_shows_where_attempts_stop_answering():
    dropoff_by_position = {row["position"]: row["attempts_reached"] for row in get_stats()["dropoff"]}
    assert dropoff_by_position == {1: 4, 2: 4, 3: 3, 4: 3, 5: 3}


def test_stats_for_unknown_lesson_returns_404():
    login_admin()
    response = client.get("/api/v1/admin/lessons/999999/stats")
    assert response.status_code == 404


def test_stats_requires_admin():
    client.cookies.clear()
    response = client.get(f"/api/v1/admin/lessons/{get_lesson_id()}/stats")
    assert response.status_code == 401
