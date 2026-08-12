import uuid

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

COURSE_SLUG = "test-course-shuffle"
SIGNED_IN_EMAIL = "shuffle-user@example.com"
SIGNED_IN_PASSWORD = "correct-horse-battery"


@pytest.fixture(autouse=True)
def seed_test_course():
    db = SessionLocal()

    course = Course(
        slug=COURSE_SLUG, title="Course For Shuffle", description="Used to test quiz shuffling.", is_published=True
    )
    db.add(course)
    db.flush()

    lesson = Lesson(
        course_id=course.id,
        position=1,
        slug=f"{COURSE_SLUG}-lesson",
        title="Lesson For Shuffle",
        description="Used to test quiz shuffling.",
        duration_seconds=300,
        is_published=True,
        required_watch_ratio=0,  # ungated: these tests cover shuffle order, not watch gating
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

    client.post(
        "/api/v1/auth/register",
        json={
            "email": SIGNED_IN_EMAIL,
            "password": SIGNED_IN_PASSWORD,
            "display_name": "Shuffle Tester",
        },
    )

    yield

    client.cookies.clear()

    db = SessionLocal()
    course_ids = select(Course.id).where(Course.slug == COURSE_SLUG)
    db.execute(delete(Attempt).where(Attempt.course_id.in_(course_ids)))
    db.execute(delete(Course).where(Course.slug == COURSE_SLUG))
    user_ids = select(User.id).where(User.email == SIGNED_IN_EMAIL)
    db.execute(delete(SessionModel).where(SessionModel.user_id.in_(user_ids)))
    db.execute(delete(User).where(User.email == SIGNED_IN_EMAIL))
    db.commit()
    db.close()


def make_attempt(seed):
    response = client.post(f"/api/v1/courses/{COURSE_SLUG}/attempts")
    assert response.status_code == 201
    attempt_id = response.json()["attempt_id"]

    db = SessionLocal()
    attempt = db.execute(select(Attempt).where(Attempt.public_id == uuid.UUID(attempt_id))).scalar_one()
    attempt.shuffle_seed = seed
    db.commit()
    db.close()
    return attempt_id


def get_quiz(attempt_id=None):
    params = {"attempt_id": attempt_id} if attempt_id else {}
    response = client.get(f"/api/v1/courses/{COURSE_SLUG}/quiz", params=params)
    assert response.status_code == 200
    return response.json()


def test_different_seeds_produce_different_question_order():
    attempt_a = make_attempt(1)
    attempt_b = make_attempt(2)

    order_a = [q["id"] for q in get_quiz(attempt_a)["questions"]]
    order_b = [q["id"] for q in get_quiz(attempt_b)["questions"]]

    assert order_a != order_b


def test_same_attempt_requested_twice_produces_identical_order():
    attempt_id = make_attempt(42)

    first = get_quiz(attempt_id)
    second = get_quiz(attempt_id)

    first_order = [(q["id"], [c["id"] for c in q["choices"]]) for q in first["questions"]]
    second_order = [(q["id"], [c["id"] for c in q["choices"]]) for q in second["questions"]]
    assert first_order == second_order


def test_shuffle_drops_nothing_and_duplicates_nothing():
    attempt_id = make_attempt(7)
    unshuffled = get_quiz()
    shuffled = get_quiz(attempt_id)

    assert sorted(q["id"] for q in shuffled["questions"]) == sorted(q["id"] for q in unshuffled["questions"])

    for question in shuffled["questions"]:
        matching = next(q for q in unshuffled["questions"] if q["id"] == question["id"])
        assert sorted(c["id"] for c in question["choices"]) == sorted(c["id"] for c in matching["choices"])
        assert len(question["choices"]) == len(matching["choices"])


def test_unknown_attempt_id_returns_404():
    response = client.get(f"/api/v1/courses/{COURSE_SLUG}/quiz", params={"attempt_id": str(uuid.uuid4())})
    assert response.status_code == 404
