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

COURSE_SLUG = "test-course-attempts"
SIGNED_IN_EMAIL = "attempts-user@example.com"
SIGNED_IN_PASSWORD = "correct-horse-battery"


@pytest.fixture(autouse=True)
def seed_test_course():
    db = SessionLocal()

    course = Course(
        slug=COURSE_SLUG,
        title="Course For Attempts",
        description="Used to test the attempts endpoints.",
        is_published=True,
    )
    db.add(course)
    db.flush()

    lesson = Lesson(
        course_id=course.id,
        position=1,
        slug=f"{COURSE_SLUG}-lesson",
        title="Lesson For Attempts",
        description="Used to test the attempts endpoints.",
        duration_seconds=300,
        is_published=True,
        required_watch_ratio=0,  # ungated: these tests cover scoring, not watch gating
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
    course_ids = select(Course.id).where(Course.slug == COURSE_SLUG)
    db.execute(delete(Attempt).where(Attempt.course_id.in_(course_ids)))
    db.execute(delete(Course).where(Course.slug == COURSE_SLUG))
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
        .join(Course)
        .where(Course.slug == COURSE_SLUG)
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


def ensure_signed_in():
    if "session_id" in client.cookies:
        return
    client.post(
        "/api/v1/auth/register",
        json={
            "email": SIGNED_IN_EMAIL,
            "password": SIGNED_IN_PASSWORD,
            "display_name": "Attempts Tester",
        },
    )


def start_attempt():
    ensure_signed_in()
    response = client.post(f"/api/v1/courses/{COURSE_SLUG}/attempts")
    assert response.status_code == 201
    return response.json()["attempt_id"]


def answer(attempt_id, question_id, choice_id):
    return client.post(
        f"/api/v1/attempts/{attempt_id}/answers",
        json={"question_id": question_id, "choice_id": choice_id},
    )


def test_starting_an_attempt_returns_a_uuid_and_question_count():
    ensure_signed_in()
    response = client.post(f"/api/v1/courses/{COURSE_SLUG}/attempts")
    assert response.status_code == 201
    body = response.json()
    assert uuid.UUID(body["attempt_id"])
    assert body["course_slug"] == COURSE_SLUG
    assert body["question_count"] == 5


def test_starting_an_attempt_while_signed_out_returns_401():
    response = client.post(f"/api/v1/courses/{COURSE_SLUG}/attempts")
    assert response.status_code == 401


def test_answering_all_five_correctly_gives_score_five_and_passed_true():
    attempt_id = start_attempt()
    questions = get_questions()

    for q in questions[:-1]:
        response = answer(attempt_id, q["question_id"], q["correct_choice_id"])
        assert response.status_code == 200
        assert response.json()["correct"] is True

    last = questions[-1]
    final_response = answer(attempt_id, last["question_id"], last["correct_choice_id"])
    assert final_response.status_code == 200

    result = client.get(f"/api/v1/attempts/{attempt_id}/result")
    assert result.status_code == 200
    body = result.json()
    assert body["score"] == 5
    assert body["passed"] is True


def test_answering_four_correctly_gives_score_four_and_passed_true():
    attempt_id = start_attempt()
    questions = get_questions()

    for q in questions[:4]:
        answer(attempt_id, q["question_id"], q["correct_choice_id"])
    answer(attempt_id, questions[4]["question_id"], questions[4]["wrong_choice_id"])

    result = client.get(f"/api/v1/attempts/{attempt_id}/result")
    assert result.status_code == 200
    body = result.json()
    assert body["score"] == 4
    assert body["passed"] is True


def test_answering_three_correctly_gives_score_three_and_passed_false():
    attempt_id = start_attempt()
    questions = get_questions()

    for q in questions[:3]:
        answer(attempt_id, q["question_id"], q["correct_choice_id"])
    for q in questions[3:]:
        answer(attempt_id, q["question_id"], q["wrong_choice_id"])

    result = client.get(f"/api/v1/attempts/{attempt_id}/result")
    assert result.status_code == 200
    body = result.json()
    assert body["score"] == 3
    assert body["passed"] is False


# REPLAY TEST: this is the guard that replaces the feature 005 hole where an
# answer could be resubmitted to discover the correct choice. Answering the
# same question twice within one attempt must be rejected.
def test_answering_the_same_question_twice_returns_409():
    attempt_id = start_attempt()
    questions = get_questions()
    q = questions[0]

    first = answer(attempt_id, q["question_id"], q["correct_choice_id"])
    assert first.status_code == 200

    second = answer(attempt_id, q["question_id"], q["wrong_choice_id"])
    assert second.status_code == 409


def test_answering_after_attempt_is_complete_returns_409():
    attempt_id = start_attempt()
    questions = get_questions()

    for q in questions:
        answer(attempt_id, q["question_id"], q["correct_choice_id"])

    extra = answer(attempt_id, questions[0]["question_id"], questions[0]["wrong_choice_id"])
    assert extra.status_code == 409


def test_reading_result_before_completion_returns_409():
    attempt_id = start_attempt()
    questions = get_questions()
    answer(attempt_id, questions[0]["question_id"], questions[0]["correct_choice_id"])

    response = client.get(f"/api/v1/attempts/{attempt_id}/result")
    assert response.status_code == 409


def test_unknown_attempt_id_returns_404():
    response = client.get(f"/api/v1/attempts/{uuid.uuid4()}/result")
    assert response.status_code == 404

    answer_response = answer(uuid.uuid4(), 1, 1)
    assert answer_response.status_code == 404


def test_choice_from_another_question_returns_400():
    attempt_id = start_attempt()
    questions = get_questions()

    response = answer(attempt_id, questions[0]["question_id"], questions[1]["correct_choice_id"])
    assert response.status_code == 400


def test_a_signed_in_users_completed_attempt_appears_in_me_attempts():
    client.post(
        "/api/v1/auth/register",
        json={
            "email": SIGNED_IN_EMAIL,
            "password": SIGNED_IN_PASSWORD,
            "display_name": "Attempts Tester",
        },
    )

    attempt_id = start_attempt()
    for q in get_questions():
        answer(attempt_id, q["question_id"], q["correct_choice_id"])

    response = client.get("/api/v1/me/attempts")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["attempt_id"] == attempt_id
    assert body[0]["course_slug"] == COURSE_SLUG
    assert body[0]["score"] == 5
    assert body[0]["passed"] is True
    assert body[0]["certificate_code"] is None


def test_me_attempts_without_a_cookie_returns_401():
    response = client.get("/api/v1/me/attempts")
    assert response.status_code == 401


LARGE_COURSE_SLUG = "test-course-attempts-large"


@pytest.fixture
def large_course():
    db = SessionLocal()
    course = Course(
        slug=LARGE_COURSE_SLUG,
        title="Course With Fifteen Questions",
        description="Used to test the 80% pass ratio beyond five questions.",
        is_published=True,
    )
    db.add(course)
    db.flush()

    for lesson_position in range(1, 4):
        lesson = Lesson(
            course_id=course.id,
            position=lesson_position,
            slug=f"{LARGE_COURSE_SLUG}-lesson-{lesson_position}",
            title=f"Lesson {lesson_position}",
            description="d",
            duration_seconds=300,
            is_published=True,
            required_watch_ratio=0,
        )
        db.add(lesson)
        db.flush()
        for q_position in range(1, 6):
            question = Question(lesson_id=lesson.id, prompt=f"Q{q_position}?", position=q_position)
            question.choices = [
                Choice(text=f"Choice {letter}", is_correct=(letter == "B"), position=index)
                for index, letter in enumerate(["A", "B", "C", "D"], start=1)
            ]
            db.add(question)

    db.commit()
    db.close()

    yield

    db = SessionLocal()
    course_ids = select(Course.id).where(Course.slug == LARGE_COURSE_SLUG)
    db.execute(delete(Attempt).where(Attempt.course_id.in_(course_ids)))
    db.execute(delete(Course).where(Course.slug == LARGE_COURSE_SLUG))
    db.commit()
    db.close()


def _get_questions_for(slug):
    db = SessionLocal()
    stmt = (
        select(Question)
        .join(Lesson)
        .join(Course)
        .where(Course.slug == slug)
        .order_by(Lesson.position, Question.position)
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


def test_passing_a_fifteen_question_course_requires_twelve_of_fifteen(large_course):
    ensure_signed_in()
    response = client.post(f"/api/v1/courses/{LARGE_COURSE_SLUG}/attempts")
    assert response.status_code == 201
    assert response.json()["question_count"] == 15
    attempt_id = response.json()["attempt_id"]

    questions = _get_questions_for(LARGE_COURSE_SLUG)
    for q in questions[:11]:
        answer(attempt_id, q["question_id"], q["correct_choice_id"])
    for q in questions[11:]:
        answer(attempt_id, q["question_id"], q["wrong_choice_id"])

    result = client.get(f"/api/v1/attempts/{attempt_id}/result").json()
    assert result["score"] == 11
    assert result["passed"] is False


def test_passing_a_fifteen_question_course_at_twelve_succeeds(large_course):
    ensure_signed_in()
    response = client.post(f"/api/v1/courses/{LARGE_COURSE_SLUG}/attempts")
    attempt_id = response.json()["attempt_id"]

    questions = _get_questions_for(LARGE_COURSE_SLUG)
    for q in questions[:12]:
        answer(attempt_id, q["question_id"], q["correct_choice_id"])
    for q in questions[12:]:
        answer(attempt_id, q["question_id"], q["wrong_choice_id"])

    result = client.get(f"/api/v1/attempts/{attempt_id}/result").json()
    assert result["score"] == 12
    assert result["passed"] is True
