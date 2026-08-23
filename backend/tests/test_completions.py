import csv
import io
from datetime import datetime, timedelta, timezone
from decimal import Decimal

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

SLUG_PREFIX = "test-completions"
ADMIN_EMAIL = "admin-completions@example.com"
PARTICIPANT_A_EMAIL = "completions-a@example.com"
PARTICIPANT_B_EMAIL = "completions-b@example.com"
PASSWORD = "correct-horse-battery"


def _make_course(slug_suffix, credit_award):
    db = SessionLocal()
    course = Course(
        slug=f"{SLUG_PREFIX}-{slug_suffix}",
        title=f"Completions Course {slug_suffix}",
        description="Used to test the completions view.",
        is_published=True,
        credit_award=credit_award,
    )
    db.add(course)
    db.flush()
    lesson = Lesson(
        course_id=course.id,
        position=1,
        slug=f"{SLUG_PREFIX}-lesson-{slug_suffix}",
        title="Completions lesson",
        description="Used to test the completions view.",
        duration_seconds=300,
        is_published=True,
        required_watch_ratio=0,
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
    course_id = course.id
    db.close()
    return course_id


@pytest.fixture(autouse=True)
def cleanup():
    client.cookies.clear()
    yield
    client.cookies.clear()
    db = SessionLocal()
    emails = [ADMIN_EMAIL, PARTICIPANT_A_EMAIL, PARTICIPANT_B_EMAIL]
    course_ids = select(Course.id).where(Course.slug.like(f"{SLUG_PREFIX}%"))
    user_ids = select(User.id).where(User.email.in_(emails))
    db.execute(delete(Attempt).where(Attempt.course_id.in_(course_ids)))
    db.execute(delete(Course).where(Course.slug.like(f"{SLUG_PREFIX}%")))
    db.execute(delete(SessionModel).where(SessionModel.user_id.in_(user_ids)))
    db.execute(delete(User).where(User.email.in_(emails)))
    db.commit()
    db.close()


def register_and_login(email, display_name, is_admin=False):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "display_name": display_name},
    )
    if response.status_code != 201:
        # Already registered by an earlier call in this test - log back in,
        # since claim()/complete_attempt() clear cookies between calls.
        client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    if is_admin:
        db = SessionLocal()
        user = db.execute(select(User).where(User.email == email)).scalar_one()
        user.is_admin = True
        db.commit()
        db.close()


def login_admin():
    register_and_login(ADMIN_EMAIL, "Completions Admin", is_admin=True)


def get_questions(course_id):
    db = SessionLocal()
    stmt = select(Question).join(Lesson).where(Lesson.course_id == course_id).order_by(Question.position)
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


def slug_for(course_id):
    db = SessionLocal()
    slug = db.execute(select(Course.slug).where(Course.id == course_id)).scalar_one()
    db.close()
    return slug


def complete_attempt(course_id, email, display_name, pass_it):
    register_and_login(email, display_name)
    response = client.post(f"/api/v1/courses/{slug_for(course_id)}/attempts")
    attempt_id = response.json()["attempt_id"]
    questions = get_questions(course_id)
    if pass_it:
        for q in questions:
            answer(attempt_id, q["question_id"], q["correct_choice_id"])
    else:
        for q in questions[:2]:
            answer(attempt_id, q["question_id"], q["correct_choice_id"])
        for q in questions[2:]:
            answer(attempt_id, q["question_id"], q["wrong_choice_id"])
    client.cookies.clear()
    return attempt_id


def claim(attempt_id, email):
    register_and_login(email, "Ignored")
    response = client.post(f"/api/v1/attempts/{attempt_id}/certificate", json={})
    client.cookies.clear()
    return response


def test_completions_endpoints_require_admin():
    assert client.get("/api/v1/admin/completions").status_code == 401
    assert client.get("/api/v1/admin/completions.csv").status_code == 401


def test_completions_lists_only_completed_attempts():
    course_id = _make_course("basic", Decimal("0.6"))
    login_admin()

    passed_id = complete_attempt(course_id, PARTICIPANT_A_EMAIL, "Ada Lovelace", pass_it=True)
    claim(passed_id, PARTICIPANT_A_EMAIL)
    failed_id = complete_attempt(course_id, PARTICIPANT_B_EMAIL, "Grace Hopper", pass_it=False)

    # An incomplete attempt (answers a single question, nothing more) must
    # not show up in the completions view at all.
    register_and_login("incomplete-completions@example.com", "Incomplete")
    incomplete = client.post(f"/api/v1/courses/{slug_for(course_id)}/attempts").json()
    questions = get_questions(course_id)
    answer(incomplete["attempt_id"], questions[0]["question_id"], questions[0]["correct_choice_id"])
    client.cookies.clear()

    login_admin()
    response = client.get(f"/api/v1/admin/completions?course_id={course_id}")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 2

    by_id = {row["attempt_id"]: row for row in rows}
    passed_row = by_id[passed_id]
    assert passed_row["passed"] is True
    assert passed_row["participant_name"] == "Ada Lovelace"
    assert passed_row["participant_email"] == PARTICIPANT_A_EMAIL
    assert passed_row["certificate_code"]
    assert Decimal(str(passed_row["credit_award"])) == Decimal("0.6")

    failed_row = by_id[failed_id]
    assert failed_row["passed"] is False
    assert failed_row["participant_name"] == "Grace Hopper"
    assert failed_row["certificate_code"] is None
    # A failed attempt earned no credit.
    assert failed_row["credit_award"] is None

    db = SessionLocal()
    db.execute(delete(User).where(User.email == "incomplete-completions@example.com"))
    db.commit()
    db.close()


def test_filter_by_course_excludes_other_courses():
    course_a = _make_course("course-a", Decimal("0.4"))
    course_b = _make_course("course-b", Decimal("0.4"))
    login_admin()
    complete_attempt(course_a, PARTICIPANT_A_EMAIL, "Ada Lovelace", pass_it=True)
    complete_attempt(course_b, PARTICIPANT_B_EMAIL, "Grace Hopper", pass_it=True)

    login_admin()
    response = client.get(f"/api/v1/admin/completions?course_id={course_a}")
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["course_title"] == "Completions Course course-a"


def test_filter_by_passed():
    course_id = _make_course("passed-filter", Decimal("0.4"))
    login_admin()
    complete_attempt(course_id, PARTICIPANT_A_EMAIL, "Ada Lovelace", pass_it=True)
    complete_attempt(course_id, PARTICIPANT_B_EMAIL, "Grace Hopper", pass_it=False)

    login_admin()
    passed_only = client.get(f"/api/v1/admin/completions?course_id={course_id}&passed=true").json()
    assert len(passed_only) == 1
    assert passed_only[0]["passed"] is True

    failed_only = client.get(f"/api/v1/admin/completions?course_id={course_id}&passed=false").json()
    assert len(failed_only) == 1
    assert failed_only[0]["passed"] is False


def test_filter_by_date_range():
    course_id = _make_course("date-filter", Decimal("0.4"))
    login_admin()
    attempt_id = complete_attempt(course_id, PARTICIPANT_A_EMAIL, "Ada Lovelace", pass_it=True)

    old_date = datetime.now(timezone.utc) - timedelta(days=10)
    db = SessionLocal()
    db.execute(
        Attempt.__table__.update().where(Attempt.public_id == attempt_id).values(completed_at=old_date)
    )
    db.commit()
    db.close()

    login_admin()
    in_range = client.get(
        f"/api/v1/admin/completions?course_id={course_id}"
        f"&start_date={(old_date - timedelta(days=1)).date()}"
        f"&end_date={(old_date + timedelta(days=1)).date()}"
    ).json()
    assert len(in_range) == 1

    out_of_range = client.get(
        f"/api/v1/admin/completions?course_id={course_id}"
        f"&start_date={(old_date + timedelta(days=2)).date()}"
    ).json()
    assert len(out_of_range) == 0


def test_csv_has_stable_header_and_one_row_per_completed_attempt():
    course_id = _make_course("csv", Decimal("0.4"))
    login_admin()
    complete_attempt(course_id, PARTICIPANT_A_EMAIL, "Ada Lovelace", pass_it=True)
    complete_attempt(course_id, PARTICIPANT_B_EMAIL, "Grace Hopper", pass_it=False)

    login_admin()
    response = client.get(f"/api/v1/admin/completions.csv?course_id={course_id}")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")

    reader = csv.reader(io.StringIO(response.text))
    rows = list(reader)
    assert rows[0] == [
        "attempt_id",
        "course_title",
        "participant_name",
        "participant_email",
        "credit_award",
        "completed_at",
        "passed",
        "certificate_code",
    ]
    assert len(rows) == 3
