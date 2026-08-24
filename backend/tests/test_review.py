import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.db import SessionLocal
from app.main import app
from app.models.attempt import Attempt
from app.models.choice import Choice
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.question import Question
from app.models.review_response import ReviewResponse
from app.models.session import Session as SessionModel
from app.models.user import User

client = TestClient(app)

SLUG_PREFIX = "test-review"
COURSE_SLUG = f"{SLUG_PREFIX}-course"
LESSON_SLUG = f"{SLUG_PREFIX}-lesson"
USER_A_EMAIL = "review-user-a@example.com"
USER_B_EMAIL = "review-user-b@example.com"
PASSWORD = "correct-horse-battery"

REVIEW_FEEDBACK = "Here's why that's the answer."


@pytest.fixture(autouse=True)
def setup_and_cleanup():
    client.cookies.clear()

    db = SessionLocal()
    course = Course(slug=COURSE_SLUG, title="Review Test Course", description="d", is_published=True)
    db.add(course)
    db.flush()
    lesson = Lesson(
        course_id=course.id,
        position=1,
        slug=LESSON_SLUG,
        title="Review Test Lesson",
        description="d",
        duration_seconds=300,
        is_published=True,
    )
    db.add(lesson)
    db.flush()

    review_question = Question(
        lesson_id=lesson.id,
        prompt="A review question?",
        kind="review",
        feedback=REVIEW_FEEDBACK,
        position=1,
    )
    review_question.choices = [
        Choice(text="Right", is_correct=True, position=1),
        Choice(text="Wrong", is_correct=False, position=2),
        Choice(text="Also wrong", is_correct=False, position=3),
    ]
    db.add(review_question)

    assessment_question = Question(
        lesson_id=lesson.id, prompt="An assessment question?", kind="assessment", position=2
    )
    assessment_question.choices = [
        Choice(text="Right", is_correct=True, position=1),
        Choice(text="Wrong", is_correct=False, position=2),
        Choice(text="Also wrong", is_correct=False, position=3),
    ]
    db.add(assessment_question)
    db.commit()
    db.close()

    yield

    client.cookies.clear()
    db = SessionLocal()
    emails = [USER_A_EMAIL, USER_B_EMAIL]
    user_ids = select(User.id).where(User.email.in_(emails))
    course_ids = select(Course.id).where(Course.slug == COURSE_SLUG)
    lesson_ids = select(Lesson.id).where(Lesson.course_id.in_(course_ids))
    question_ids = select(Question.id).where(Question.lesson_id.in_(lesson_ids))
    db.execute(delete(ReviewResponse).where(ReviewResponse.question_id.in_(question_ids)))
    db.execute(delete(Attempt).where(Attempt.course_id.in_(course_ids)))
    db.execute(delete(SessionModel).where(SessionModel.user_id.in_(user_ids)))
    db.execute(delete(User).where(User.email.in_(emails)))
    db.execute(delete(Course).where(Course.slug == COURSE_SLUG))
    db.commit()
    db.close()


def register_and_login(email):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "display_name": "Review Tester"},
    )
    db = SessionLocal()
    user_id = db.execute(select(User.id).where(User.email == email)).scalar_one()
    db.close()
    return user_id


def get_question_data(kind):
    db = SessionLocal()
    question = db.execute(
        select(Question)
        .join(Lesson, Lesson.id == Question.lesson_id)
        .where(Lesson.slug == LESSON_SLUG, Question.kind == kind)
        .options(selectinload(Question.choices))
    ).scalar_one()
    data = {
        "id": question.id,
        "correct_choice_id": next(c.id for c in question.choices if c.is_correct),
        "wrong_choice_id": next(c.id for c in question.choices if not c.is_correct),
    }
    db.close()
    return data


def answer_review(question_id, choice_id):
    return client.post(
        f"/api/v1/courses/{COURSE_SLUG}/lessons/{LESSON_SLUG}/review/{question_id}",
        json={"choice_id": choice_id},
    )


def test_get_review_questions_serves_only_review_kind():
    response = client.get(f"/api/v1/courses/{COURSE_SLUG}/lessons/{LESSON_SLUG}/review")
    assert response.status_code == 200
    body = response.json()
    assert len(body["questions"]) == 1
    assert body["questions"][0]["prompt"] == "A review question?"


# GUARD TEST: is_correct (and feedback, which would leak the answer through
# wording) must never appear before grading - the feature 015/006 leak-test
# rule extended to review questions.
def test_get_review_questions_never_leaks_correct_answer_or_feedback():
    response = client.get(f"/api/v1/courses/{COURSE_SLUG}/lessons/{LESSON_SLUG}/review")
    raw = response.text
    assert "is_correct" not in raw
    assert "feedback" not in raw
    assert REVIEW_FEEDBACK not in raw


def test_answering_correctly_returns_correct_true_and_the_feedback():
    question = get_question_data("review")
    response = answer_review(question["id"], question["correct_choice_id"])
    assert response.status_code == 200
    body = response.json()
    assert body["correct"] is True
    assert body["feedback"] == REVIEW_FEEDBACK


def test_answering_incorrectly_returns_correct_false():
    question = get_question_data("review")
    response = answer_review(question["id"], question["wrong_choice_id"])
    assert response.status_code == 200
    body = response.json()
    assert body["correct"] is False
    assert body["feedback"] == REVIEW_FEEDBACK


def test_answering_a_review_question_writes_no_attempt_row():
    # A delta check, not a global-emptiness assumption: this repo's dev and
    # test databases are the same one (see current-feature.md, feature
    # 028's walkthrough), so other attempts can legitimately already exist.
    # The claim under test is narrower - answering a review question adds
    # none of its own.
    question = get_question_data("review")
    before = SessionLocal().execute(select(Attempt.id)).all()
    answer_review(question["id"], question["correct_choice_id"])
    after = SessionLocal().execute(select(Attempt.id)).all()
    assert before == after


def test_reanswering_a_review_question_overwrites_not_accumulates():
    question = get_question_data("review")
    answer_review(question["id"], question["wrong_choice_id"])
    answer_review(question["id"], question["correct_choice_id"])

    db = SessionLocal()
    rows = db.execute(
        select(ReviewResponse).where(ReviewResponse.question_id == question["id"])
    ).scalars().all()
    db.close()
    assert len(rows) == 1
    assert rows[0].is_correct is True


def test_answering_the_assessment_question_via_review_endpoint_returns_404():
    # The review endpoint only serves/accepts kind='review' questions - an
    # assessment question id must not be answerable here.
    question = get_question_data("assessment")
    response = answer_review(question["id"], question["correct_choice_id"])
    assert response.status_code == 404


def test_answering_with_a_choice_from_another_question_returns_400():
    review_question = get_question_data("review")
    assessment_question = get_question_data("assessment")
    response = answer_review(review_question["id"], assessment_question["correct_choice_id"])
    assert response.status_code == 400


def test_unknown_question_id_returns_404():
    response = answer_review(999999, 1)
    assert response.status_code == 404


# LEAK TEST (feature 015's rule, carried forward to review_responses): two
# people sharing a browser must never inherit or overwrite each other's
# review answers.
def test_user_bs_review_answer_does_not_overwrite_user_as_sharing_a_browser():
    question = get_question_data("review")

    user_a_id = register_and_login(USER_A_EMAIL)
    shared_viewer_id = uuid.UUID(client.cookies["viewer_id"])
    answer_review(question["id"], question["correct_choice_id"])

    client.cookies.clear()
    client.cookies.set("viewer_id", str(shared_viewer_id))
    register_and_login(USER_B_EMAIL)
    answer_review(question["id"], question["wrong_choice_id"])

    db = SessionLocal()
    rows = db.execute(
        select(ReviewResponse).where(ReviewResponse.question_id == question["id"])
    ).scalars().all()
    db.close()

    assert len(rows) == 2
    by_user = {row.user_id: row for row in rows}
    assert by_user[user_a_id].is_correct is True
    assert by_user[user_a_id].choice_id == question["correct_choice_id"]
