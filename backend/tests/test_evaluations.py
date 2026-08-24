import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db import SessionLocal
from app.main import app
from app.models.attempt import Attempt
from app.models.choice import Choice
from app.models.course import Course
from app.models.evaluation import Evaluation
from app.models.lesson import Lesson
from app.models.question import Question
from app.models.session import Session as SessionModel
from app.models.user import User

client = TestClient(app)

COURSE_SLUG = "test-course-evaluations"
PARTICIPANT_EMAIL = "evaluations-user@example.com"
ADMIN_EMAIL = "evaluations-admin@example.com"
PASSWORD = "correct-horse-battery"

FULL_RATINGS = {
    "objectives_met": 5,
    "prerequisites_appropriate": 4,
    "materials_relevant": 5,
    "time_allotted_appropriate": 3,
}


@pytest.fixture(autouse=True)
def seed_test_course():
    client.cookies.clear()
    db = SessionLocal()

    course = Course(
        slug=COURSE_SLUG,
        title="Course For Evaluations",
        description="Used to test the evaluations endpoints.",
        is_published=True,
    )
    db.add(course)
    db.flush()

    lesson = Lesson(
        course_id=course.id,
        position=1,
        slug=f"{COURSE_SLUG}-lesson",
        title="Lesson For Evaluations",
        description="Used to test the evaluations endpoints.",
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
    db.close()

    yield

    db = SessionLocal()
    course_ids = select(Course.id).where(Course.slug == COURSE_SLUG)
    attempt_ids = select(Attempt.id).where(Attempt.course_id.in_(course_ids))
    db.execute(delete(Evaluation).where(Evaluation.attempt_id.in_(attempt_ids)))
    db.execute(delete(Attempt).where(Attempt.course_id.in_(course_ids)))
    db.execute(delete(Course).where(Course.slug == COURSE_SLUG))
    user_emails = [PARTICIPANT_EMAIL, ADMIN_EMAIL]
    user_ids = select(User.id).where(User.email.in_(user_emails))
    db.execute(delete(SessionModel).where(SessionModel.user_id.in_(user_ids)))
    db.execute(delete(User).where(User.email.in_(user_emails)))
    db.commit()
    db.close()
    client.cookies.clear()


def get_questions():
    db = SessionLocal()
    stmt = select(Question).join(Lesson).join(Course).where(Course.slug == COURSE_SLUG).order_by(Question.position)
    questions = db.execute(stmt).scalars().all()
    result = []
    for question in questions:
        correct_choice = next(c for c in question.choices if c.is_correct)
        result.append({"question_id": question.id, "correct_choice_id": correct_choice.id})
    db.close()
    return result


def login_participant():
    if "session_id" in client.cookies:
        return
    client.post(
        "/api/v1/auth/register",
        json={"email": PARTICIPANT_EMAIL, "password": PASSWORD, "display_name": "Evaluations Tester"},
    )


def login_admin():
    client.post(
        "/api/v1/auth/register",
        json={"email": ADMIN_EMAIL, "password": PASSWORD, "display_name": "Evaluations Admin"},
    )
    db = SessionLocal()
    user = db.execute(select(User).where(User.email == ADMIN_EMAIL)).scalar_one()
    user.is_admin = True
    db.commit()
    db.close()


def get_course_id():
    db = SessionLocal()
    course_id = db.execute(select(Course.id).where(Course.slug == COURSE_SLUG)).scalar_one()
    db.close()
    return course_id


def complete_attempt():
    login_participant()
    response = client.post(f"/api/v1/courses/{COURSE_SLUG}/attempts")
    attempt_id = response.json()["attempt_id"]
    for q in get_questions():
        client.post(
            f"/api/v1/attempts/{attempt_id}/answers",
            json={"question_id": q["question_id"], "choice_id": q["correct_choice_id"]},
        )
    return attempt_id


def test_evaluation_dimensions_excludes_instructor_effective_for_self_study():
    response = client.get("/api/v1/meta/evaluation-dimensions")
    assert response.status_code == 200
    keys = [dimension["key"] for dimension in response.json()["dimensions"]]
    assert "instructor_effective" not in keys
    assert keys == ["objectives_met", "prerequisites_appropriate", "materials_relevant", "time_allotted_appropriate"]


def test_submitting_on_a_completed_attempt_stores_every_dimension():
    attempt_id = complete_attempt()

    response = client.post(f"/api/v1/attempts/{attempt_id}/evaluation", json={**FULL_RATINGS, "comments": "Great course."})
    assert response.status_code == 200
    body = response.json()
    assert body["objectives_met"] == 5
    assert body["prerequisites_appropriate"] == 4
    assert body["materials_relevant"] == 5
    assert body["time_allotted_appropriate"] == 3
    assert body["comments"] == "Great course."
    assert body["submitted_at"]


def test_submitting_on_an_incomplete_attempt_is_refused():
    login_participant()
    response = client.post(f"/api/v1/courses/{COURSE_SLUG}/attempts")
    attempt_id = response.json()["attempt_id"]

    response = client.post(f"/api/v1/attempts/{attempt_id}/evaluation", json=FULL_RATINGS)
    assert response.status_code == 409


def test_a_second_submission_for_the_same_attempt_is_refused_cleanly():
    attempt_id = complete_attempt()

    first = client.post(f"/api/v1/attempts/{attempt_id}/evaluation", json=FULL_RATINGS)
    assert first.status_code == 200

    second = client.post(f"/api/v1/attempts/{attempt_id}/evaluation", json=FULL_RATINGS)
    assert second.status_code == 409


def test_a_partial_submission_with_three_of_five_dimensions_is_accepted():
    attempt_id = complete_attempt()

    response = client.post(
        f"/api/v1/attempts/{attempt_id}/evaluation",
        json={"objectives_met": 4, "materials_relevant": 3, "time_allotted_appropriate": 5},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["objectives_met"] == 4
    assert body["prerequisites_appropriate"] is None
    assert body["materials_relevant"] == 3
    assert body["time_allotted_appropriate"] == 5


@pytest.mark.parametrize("rating", [0, 6])
def test_a_rating_outside_one_to_five_is_refused(rating):
    attempt_id = complete_attempt()

    response = client.post(f"/api/v1/attempts/{attempt_id}/evaluation", json={"objectives_met": rating})
    assert response.status_code == 422


def test_evaluation_not_found_for_an_attempt_that_has_not_submitted_one():
    attempt_id = complete_attempt()

    response = client.get(f"/api/v1/attempts/{attempt_id}/evaluation")
    assert response.status_code == 200
    assert response.json() is None


def test_submitted_evaluation_shows_back_on_reload():
    attempt_id = complete_attempt()
    client.post(f"/api/v1/attempts/{attempt_id}/evaluation", json={**FULL_RATINGS, "comments": "Solid."})

    response = client.get(f"/api/v1/attempts/{attempt_id}/evaluation")
    assert response.status_code == 200
    body = response.json()
    assert body["objectives_met"] == 5
    assert body["comments"] == "Solid."


def test_unknown_attempt_id_returns_404():
    response = client.get(f"/api/v1/attempts/{uuid.uuid4()}/evaluation")
    assert response.status_code == 404

    response = client.post(f"/api/v1/attempts/{uuid.uuid4()}/evaluation", json=FULL_RATINGS)
    assert response.status_code == 404


def test_course_summary_computes_means_over_submitted_values_only_ignoring_nulls():
    first_attempt = complete_attempt()
    client.post(
        f"/api/v1/attempts/{first_attempt}/evaluation",
        json={"objectives_met": 5, "materials_relevant": 3},
    )
    second_attempt = complete_attempt()
    client.post(f"/api/v1/attempts/{second_attempt}/evaluation", json={"objectives_met": 3})

    login_admin()
    response = client.get(f"/api/v1/admin/courses/{get_course_id()}/evaluations")
    assert response.status_code == 200
    means = {row["key"]: row["mean"] for row in response.json()["summary"]["means"]}
    assert means["objectives_met"] == pytest.approx(4.0)
    assert means["materials_relevant"] == pytest.approx(3.0)
    assert means["prerequisites_appropriate"] is None


def test_response_rate_counts_completed_attempts_as_the_denominator():
    # One completed attempt gets an evaluation, one completed attempt doesn't.
    first_attempt = complete_attempt()
    client.post(f"/api/v1/attempts/{first_attempt}/evaluation", json=FULL_RATINGS)
    complete_attempt()

    login_admin()
    response = client.get(f"/api/v1/admin/courses/{get_course_id()}/evaluations")
    assert response.status_code == 200
    summary = response.json()["summary"]
    assert summary["response_count"] == 1
    assert summary["completed_attempts_count"] == 2
    assert summary["response_rate"] == pytest.approx(0.5)


def test_course_with_no_responses_shows_zero_counts_and_no_comments():
    login_admin()
    response = client.get(f"/api/v1/admin/courses/{get_course_id()}/evaluations")
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["response_count"] == 0
    assert body["summary"]["response_rate"] is None
    assert body["comments"] == []


def test_comments_come_back_newest_first():
    first_attempt = complete_attempt()
    client.post(f"/api/v1/attempts/{first_attempt}/evaluation", json={**FULL_RATINGS, "comments": "First."})
    second_attempt = complete_attempt()
    client.post(f"/api/v1/attempts/{second_attempt}/evaluation", json={**FULL_RATINGS, "comments": "Second."})

    login_admin()
    response = client.get(f"/api/v1/admin/courses/{get_course_id()}/evaluations")
    assert response.status_code == 200
    comments = [row["comments"] for row in response.json()["comments"]]
    assert comments == ["Second.", "First."]


def test_evaluations_admin_view_requires_admin():
    response = client.get(f"/api/v1/admin/courses/{get_course_id()}/evaluations")
    assert response.status_code == 401


def test_evaluations_for_unknown_course_returns_404():
    login_admin()
    response = client.get("/api/v1/admin/courses/999999/evaluations")
    assert response.status_code == 404
