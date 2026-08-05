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

client = TestClient(app)

QUIZ_SLUG = "test-lesson-attempts"


@pytest.fixture(autouse=True)
def seed_test_lesson():
    db = SessionLocal()

    lesson = Lesson(
        slug=QUIZ_SLUG,
        title="Lesson For Attempts",
        description="Used to test the attempts endpoints.",
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
    # attempt_answers has no cascading FK to questions, so attempts (and their
    # answers, via the attempt_id cascade) must go before the lesson's
    # questions do.
    lesson_ids = select(Lesson.id).where(Lesson.slug == QUIZ_SLUG)
    db.execute(delete(Attempt).where(Attempt.lesson_id.in_(lesson_ids)))
    db.execute(delete(Lesson).where(Lesson.slug == QUIZ_SLUG))
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


def start_attempt():
    response = client.post(f"/api/v1/lessons/{QUIZ_SLUG}/attempts")
    assert response.status_code == 201
    return response.json()["attempt_id"]


def answer(attempt_id, question_id, choice_id):
    return client.post(
        f"/api/v1/attempts/{attempt_id}/answers",
        json={"question_id": question_id, "choice_id": choice_id},
    )


def test_starting_an_attempt_returns_a_uuid_and_question_count():
    response = client.post(f"/api/v1/lessons/{QUIZ_SLUG}/attempts")
    assert response.status_code == 201
    body = response.json()
    assert uuid.UUID(body["attempt_id"])
    assert body["lesson_slug"] == QUIZ_SLUG
    assert body["question_count"] == 5


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
