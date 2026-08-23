import uuid
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
            feedback=f"Feedback for question {position}.",
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

    for index, q in enumerate(questions[:-1], start=1):
        response = answer(attempt_id, q["question_id"], q["correct_choice_id"])
        assert response.status_code == 200
        assert response.json()["answered_count"] == index

    last = questions[-1]
    final_response = answer(attempt_id, last["question_id"], last["correct_choice_id"])
    assert final_response.status_code == 200

    result = client.get(f"/api/v1/attempts/{attempt_id}/result")
    assert result.status_code == 200
    body = result.json()
    assert body["score"] == 5
    assert body["passed"] is True


# GUARD TEST: 6.01.2, no-test-bank arm - the application cannot know whether
# an in-progress attempt will pass, so no per-question correctness may
# appear in an answer response mid-attempt (Part 4 of current-feature.md).
def test_in_progress_answer_response_carries_no_correctness():
    attempt_id = start_attempt()
    questions = get_questions()

    response = answer(attempt_id, questions[0]["question_id"], questions[0]["correct_choice_id"])
    assert response.status_code == 200
    assert set(response.json().keys()) == {"answered_count", "question_count"}


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
        description="Used to test the default 70% pass ratio beyond five questions.",
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


def test_passing_a_fifteen_question_course_requires_eleven_of_fifteen(large_course):
    # Feature 023: the pass mark is the course's pass_ratio (default 0.70)
    # applied to the assessment question count, not a hardcoded 80% - here
    # ceil(0.70 * 15) == 11, not the old ceil(0.80 * 15) == 12.
    ensure_signed_in()
    response = client.post(f"/api/v1/courses/{LARGE_COURSE_SLUG}/attempts")
    assert response.status_code == 201
    assert response.json()["question_count"] == 15
    attempt_id = response.json()["attempt_id"]

    questions = _get_questions_for(LARGE_COURSE_SLUG)
    for q in questions[:10]:
        answer(attempt_id, q["question_id"], q["correct_choice_id"])
    for q in questions[10:]:
        answer(attempt_id, q["question_id"], q["wrong_choice_id"])

    result = client.get(f"/api/v1/attempts/{attempt_id}/result").json()
    assert result["score"] == 10
    assert result["passed"] is False


def test_passing_a_fifteen_question_course_at_eleven_succeeds(large_course):
    ensure_signed_in()
    response = client.post(f"/api/v1/courses/{LARGE_COURSE_SLUG}/attempts")
    attempt_id = response.json()["attempt_id"]

    questions = _get_questions_for(LARGE_COURSE_SLUG)
    for q in questions[:11]:
        answer(attempt_id, q["question_id"], q["correct_choice_id"])
    for q in questions[11:]:
        answer(attempt_id, q["question_id"], q["wrong_choice_id"])

    result = client.get(f"/api/v1/attempts/{attempt_id}/result").json()
    assert result["score"] == 11
    assert result["passed"] is True


# GUARD TEST: 6.01.2, no-test-bank arm - "on a failed assessment, the CPE
# program sponsor may not provide feedback to the test taker." A failed
# result must carry a score and nothing that identifies which answers were
# right or wrong, anywhere in the payload.
def test_a_failed_result_exposes_no_per_question_correctness():
    attempt_id = start_attempt()
    questions = get_questions()
    for q in questions:
        answer(attempt_id, q["question_id"], q["wrong_choice_id"])

    response = client.get(f"/api/v1/attempts/{attempt_id}/result")
    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is False
    assert body["answers"] is None
    assert "chosen_choice_id" not in response.text
    assert "correct_choice_id" not in response.text
    # 6.01.2 sub-ii b: on a failed assessment, no feedback either - the
    # whole per-question list is omitted, so its feedback text goes with it.
    assert "feedback" not in response.text.lower()


def test_a_passed_result_may_include_the_per_question_breakdown():
    attempt_id = start_attempt()
    questions = get_questions()
    for q in questions:
        answer(attempt_id, q["question_id"], q["correct_choice_id"])

    response = client.get(f"/api/v1/attempts/{attempt_id}/result")
    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is True
    assert len(body["answers"]) == 5
    for index, (entry, q) in enumerate(zip(body["answers"], questions), start=1):
        assert entry["is_correct"] is True
        assert entry["chosen_choice_id"] == q["correct_choice_id"]
        assert entry["correct_choice_id"] == q["correct_choice_id"]
        # 6.01.2 sub-ii b: on a passed assessment, a sponsor may provide
        # feedback - the seed fixture writes one per question.
        assert entry["feedback"] == f"Feedback for question {index}."


CUSTOM_RATIO_COURSE_SLUG = "test-course-attempts-custom-ratio"


@pytest.fixture
def custom_ratio_course():
    db = SessionLocal()
    course = Course(
        slug=CUSTOM_RATIO_COURSE_SLUG,
        title="Course With A Stricter Pass Ratio",
        description="Used to prove the pass mark comes from course.pass_ratio, not a hardcoded default.",
        is_published=True,
        pass_ratio=Decimal("0.90"),
    )
    db.add(course)
    db.flush()

    lesson = Lesson(
        course_id=course.id,
        position=1,
        slug=f"{CUSTOM_RATIO_COURSE_SLUG}-lesson",
        title="Lesson",
        description="d",
        duration_seconds=300,
        is_published=True,
        required_watch_ratio=0,
    )
    db.add(lesson)
    db.flush()
    for position in range(1, 6):
        question = Question(lesson_id=lesson.id, prompt=f"Q{position}?", position=position)
        question.choices = [
            Choice(text=f"Choice {letter}", is_correct=(letter == "B"), position=index)
            for index, letter in enumerate(["A", "B", "C", "D"], start=1)
        ]
        db.add(question)

    db.commit()
    db.close()

    yield

    db = SessionLocal()
    course_ids = select(Course.id).where(Course.slug == CUSTOM_RATIO_COURSE_SLUG)
    db.execute(delete(Attempt).where(Attempt.course_id.in_(course_ids)))
    db.execute(delete(Course).where(Course.slug == CUSTOM_RATIO_COURSE_SLUG))
    db.commit()
    db.close()


def test_pass_mark_uses_the_courses_pass_ratio_not_a_hardcoded_default(custom_ratio_course):
    # ceil(0.90 * 5) == 5: with this course's stricter ratio, four of five
    # correct - a pass under the default 0.70 ratio - must fail here.
    ensure_signed_in()
    response = client.post(f"/api/v1/courses/{CUSTOM_RATIO_COURSE_SLUG}/attempts")
    assert response.status_code == 201
    attempt_id = response.json()["attempt_id"]

    questions = _get_questions_for(CUSTOM_RATIO_COURSE_SLUG)
    for q in questions[:4]:
        answer(attempt_id, q["question_id"], q["correct_choice_id"])
    answer(attempt_id, questions[4]["question_id"], questions[4]["wrong_choice_id"])

    result = client.get(f"/api/v1/attempts/{attempt_id}/result").json()
    assert result["score"] == 4
    assert result["passed"] is False
