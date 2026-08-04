import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db import SessionLocal
from app.main import app
from app.models.choice import Choice
from app.models.lesson import Lesson
from app.models.question import Question

client = TestClient(app)

WITH_QUIZ_SLUG = "test-lesson-with-quiz"
WITHOUT_QUIZ_SLUG = "test-lesson-without-quiz"
OTHER_QUIZ_SLUG = "test-lesson-other-quiz"

ALL_TEST_SLUGS = [WITH_QUIZ_SLUG, WITHOUT_QUIZ_SLUG, OTHER_QUIZ_SLUG]


@pytest.fixture(autouse=True)
def seed_test_lessons():
    db = SessionLocal()

    lesson_with_quiz = Lesson(
        slug=WITH_QUIZ_SLUG,
        title="Lesson With Quiz",
        description="Used to test the quiz endpoint.",
        duration_seconds=300,
        is_published=True,
    )
    db.add(lesson_with_quiz)
    db.flush()

    for position in range(1, 6):
        question = Question(
            lesson_id=lesson_with_quiz.id,
            prompt=f"Question {position}?",
            position=position,
        )
        question.choices = [
            Choice(text=f"Choice {letter}", is_correct=(letter == "B"), position=index)
            for index, letter in enumerate(["A", "B", "C", "D"], start=1)
        ]
        db.add(question)

    db.add(
        Lesson(
            slug=WITHOUT_QUIZ_SLUG,
            title="Lesson Without Quiz",
            description="Used to test the no-quiz-yet case.",
            duration_seconds=300,
            is_published=True,
        )
    )

    other_lesson = Lesson(
        slug=OTHER_QUIZ_SLUG,
        title="Other Lesson With Quiz",
        description="Used to test cross-lesson question access.",
        duration_seconds=300,
        is_published=True,
    )
    db.add(other_lesson)
    db.flush()

    other_question = Question(lesson_id=other_lesson.id, prompt="Other question?", position=1)
    other_question.choices = [
        Choice(text=f"Choice {letter}", is_correct=(letter == "B"), position=index)
        for index, letter in enumerate(["A", "B", "C", "D"], start=1)
    ]
    db.add(other_question)

    db.commit()
    db.close()

    yield

    db = SessionLocal()
    db.execute(delete(Lesson).where(Lesson.slug.in_(ALL_TEST_SLUGS)))
    db.commit()
    db.close()


def get_question(slug, position=1):
    db = SessionLocal()
    stmt = (
        select(Question)
        .join(Lesson)
        .where(Lesson.slug == slug, Question.position == position)
    )
    question = db.execute(stmt).scalar_one()
    correct_choice = next(c for c in question.choices if c.is_correct)
    wrong_choice = next(c for c in question.choices if not c.is_correct)
    result = {
        "question_id": question.id,
        "correct_choice_id": correct_choice.id,
        "wrong_choice_id": wrong_choice.id,
    }
    db.close()
    return result


def test_quiz_returns_five_questions_with_four_choices_each():
    response = client.get(f"/api/v1/lessons/{WITH_QUIZ_SLUG}/quiz")
    assert response.status_code == 200
    body = response.json()
    assert body["question_count"] == 5
    assert len(body["questions"]) == 5
    for question in body["questions"]:
        assert len(question["choices"]) == 4


# GUARD TEST: this must never be deleted or weakened. It is the only thing
# standing between "quiz answers stripped out" and "quiz answers leaked to
# every browser that loads this page." If this starts failing, the bug is in
# the API response, not the test.
def test_quiz_response_never_leaks_correct_answer():
    response = client.get(f"/api/v1/lessons/{WITH_QUIZ_SLUG}/quiz")
    assert response.status_code == 200
    raw = response.text
    assert "is_correct" not in raw
    assert "true" not in raw
    assert "correct" not in raw.lower()


def test_quiz_questions_and_choices_ordered_by_position():
    response = client.get(f"/api/v1/lessons/{WITH_QUIZ_SLUG}/quiz")
    body = response.json()
    positions = [q["position"] for q in body["questions"]]
    assert positions == sorted(positions)
    for question in body["questions"]:
        choice_positions = [c["position"] for c in question["choices"]]
        assert choice_positions == sorted(choice_positions)


def test_lesson_with_no_questions_returns_404():
    response = client.get(f"/api/v1/lessons/{WITHOUT_QUIZ_SLUG}/quiz")
    assert response.status_code == 404
    assert response.json()["detail"] == "This lesson has no quiz yet"


def test_unknown_slug_returns_404():
    response = client.get("/api/v1/lessons/does-not-exist/quiz")
    assert response.status_code == 404


def test_correct_answer_returns_correct_true():
    q = get_question(WITH_QUIZ_SLUG, position=1)
    response = client.post(
        f"/api/v1/lessons/{WITH_QUIZ_SLUG}/quiz/answers",
        json={"question_id": q["question_id"], "choice_id": q["correct_choice_id"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["correct"] is True
    assert body["correct_choice_id"] == q["correct_choice_id"]


def test_incorrect_answer_returns_correct_false_and_reveals_answer():
    q = get_question(WITH_QUIZ_SLUG, position=1)
    response = client.post(
        f"/api/v1/lessons/{WITH_QUIZ_SLUG}/quiz/answers",
        json={"question_id": q["question_id"], "choice_id": q["wrong_choice_id"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["correct"] is False
    assert body["correct_choice_id"] == q["correct_choice_id"]


def test_choice_from_different_question_returns_400():
    q1 = get_question(WITH_QUIZ_SLUG, position=1)
    q2 = get_question(WITH_QUIZ_SLUG, position=2)
    response = client.post(
        f"/api/v1/lessons/{WITH_QUIZ_SLUG}/quiz/answers",
        json={"question_id": q1["question_id"], "choice_id": q2["correct_choice_id"]},
    )
    assert response.status_code == 400


def test_question_from_different_lesson_returns_404():
    other = get_question(OTHER_QUIZ_SLUG, position=1)
    response = client.post(
        f"/api/v1/lessons/{WITH_QUIZ_SLUG}/quiz/answers",
        json={"question_id": other["question_id"], "choice_id": other["correct_choice_id"]},
    )
    assert response.status_code == 404


def test_unknown_question_id_returns_404():
    response = client.post(
        f"/api/v1/lessons/{WITH_QUIZ_SLUG}/quiz/answers",
        json={"question_id": 9999999, "choice_id": 1},
    )
    assert response.status_code == 404
