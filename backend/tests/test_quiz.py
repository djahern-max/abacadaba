import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db import SessionLocal
from app.main import app
from app.models.choice import Choice
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.question import Question

client = TestClient(app)

WITH_QUIZ_SLUG = "test-course-with-quiz"
WITHOUT_QUIZ_SLUG = "test-course-without-quiz"
MULTI_LESSON_SLUG = "test-course-multi-lesson-quiz"
MIXED_KIND_SLUG = "test-course-mixed-kind-quiz"

ALL_TEST_SLUGS = [WITH_QUIZ_SLUG, WITHOUT_QUIZ_SLUG, MULTI_LESSON_SLUG, MIXED_KIND_SLUG]


def _add_lesson_with_questions(db, course_id, slug, position, question_count=5):
    lesson = Lesson(
        course_id=course_id,
        position=position,
        slug=slug,
        title=f"Lesson {slug}",
        description="Used to test the quiz endpoint.",
        duration_seconds=300,
        is_published=True,
    )
    db.add(lesson)
    db.flush()

    for q_position in range(1, question_count + 1):
        question = Question(
            lesson_id=lesson.id,
            prompt=f"Question {q_position}?",
            position=q_position,
            # Feature 023a: feedback is written on assessment questions too
            # (shown on a pass) - the leak test below needs it present to be
            # a meaningful guard against it leaking mid-attempt.
            feedback=f"Feedback for question {q_position}.",
        )
        question.choices = [
            Choice(text=f"Choice {letter}", is_correct=(letter == "B"), position=index)
            for index, letter in enumerate(["A", "B", "C", "D"], start=1)
        ]
        db.add(question)
    db.flush()
    return lesson


@pytest.fixture(autouse=True)
def seed_test_courses():
    db = SessionLocal()

    with_quiz = Course(slug=WITH_QUIZ_SLUG, title="Course With Quiz", description="d", is_published=True)
    db.add(with_quiz)
    db.flush()
    _add_lesson_with_questions(db, with_quiz.id, f"{WITH_QUIZ_SLUG}-lesson", position=1)

    without_quiz = Course(slug=WITHOUT_QUIZ_SLUG, title="Course Without Quiz", description="d", is_published=True)
    db.add(without_quiz)
    db.flush()
    db.add(
        Lesson(
            course_id=without_quiz.id,
            position=1,
            slug=f"{WITHOUT_QUIZ_SLUG}-lesson",
            title="Lesson without questions",
            description="Used to test the no-quiz-yet case.",
            duration_seconds=300,
            is_published=True,
        )
    )

    multi = Course(slug=MULTI_LESSON_SLUG, title="Course With Multiple Lessons", description="d", is_published=True)
    db.add(multi)
    db.flush()
    _add_lesson_with_questions(db, multi.id, f"{MULTI_LESSON_SLUG}-a", position=1, question_count=2)
    _add_lesson_with_questions(db, multi.id, f"{MULTI_LESSON_SLUG}-b", position=2, question_count=3)

    mixed = Course(slug=MIXED_KIND_SLUG, title="Course With Review And Assessment", description="d", is_published=True)
    db.add(mixed)
    db.flush()
    mixed_lesson = Lesson(
        course_id=mixed.id,
        position=1,
        slug=f"{MIXED_KIND_SLUG}-lesson",
        title="Lesson with review and assessment questions",
        description="Used to test that the quiz serves assessment questions only.",
        duration_seconds=300,
        is_published=True,
    )
    db.add(mixed_lesson)
    db.flush()
    for position, kind in enumerate(["review", "review", "assessment", "assessment", "assessment"], start=1):
        question = Question(lesson_id=mixed_lesson.id, prompt=f"{kind} question {position}?", kind=kind, position=position)
        question.choices = [
            Choice(text=f"Choice {letter}", is_correct=(letter == "B"), position=index)
            for index, letter in enumerate(["A", "B", "C", "D"], start=1)
        ]
        db.add(question)

    db.commit()
    db.close()

    yield

    db = SessionLocal()
    db.execute(delete(Course).where(Course.slug.in_(ALL_TEST_SLUGS)))
    db.commit()
    db.close()


def test_quiz_returns_five_questions_with_four_choices_each():
    response = client.get(f"/api/v1/courses/{WITH_QUIZ_SLUG}/quiz")
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
#
# Feature 023a: feedback text routinely states the answer ("a pH of 1.4
# falls below the corrosivity threshold of 2.0" identifies the correct
# choice as surely as is_correct does), so it's checked here too - the
# fixture's questions all carry feedback text specifically so this guard
# means something. QuestionPublic (app/schemas/quiz.py) never defines a
# feedback field at all, following 004's precedent: a schema that omits the
# field, not one that filters it out at serialization time.
def test_quiz_response_never_leaks_correct_answer():
    response = client.get(f"/api/v1/courses/{WITH_QUIZ_SLUG}/quiz")
    assert response.status_code == 200
    raw = response.text
    assert "is_correct" not in raw
    assert "true" not in raw
    assert "correct" not in raw.lower()
    assert "feedback" not in raw.lower()


def test_quiz_questions_and_choices_ordered_by_position():
    response = client.get(f"/api/v1/courses/{WITH_QUIZ_SLUG}/quiz")
    body = response.json()
    positions = [q["position"] for q in body["questions"]]
    assert positions == sorted(positions)
    for question in body["questions"]:
        choice_positions = [c["position"] for c in question["choices"]]
        assert choice_positions == sorted(choice_positions)


def test_quiz_spanning_lessons_is_ordered_lesson_then_question_position():
    response = client.get(f"/api/v1/courses/{MULTI_LESSON_SLUG}/quiz")
    body = response.json()
    assert body["question_count"] == 5
    prompts = [q["prompt"] for q in body["questions"]]
    # Lesson a (position 1) contributes its two questions before lesson b
    # (position 2) contributes its three, in each lesson's question order.
    assert prompts == ["Question 1?", "Question 2?", "Question 1?", "Question 2?", "Question 3?"]


# Feature 023: the qualified assessment serves assessment questions only -
# review questions are served separately, at segment boundaries.
def test_quiz_serves_assessment_questions_only():
    response = client.get(f"/api/v1/courses/{MIXED_KIND_SLUG}/quiz")
    assert response.status_code == 200
    body = response.json()
    assert body["question_count"] == 3
    prompts = [q["prompt"] for q in body["questions"]]
    assert prompts == ["assessment question 3?", "assessment question 4?", "assessment question 5?"]


def test_course_with_no_questions_returns_404():
    response = client.get(f"/api/v1/courses/{WITHOUT_QUIZ_SLUG}/quiz")
    assert response.status_code == 404
    assert response.json()["detail"] == "This course has no assessment yet"


def test_unknown_slug_returns_404():
    response = client.get("/api/v1/courses/does-not-exist/quiz")
    assert response.status_code == 404


def test_old_answers_endpoint_is_gone():
    response = client.post(
        f"/api/v1/courses/{WITH_QUIZ_SLUG}/quiz/answers",
        json={"question_id": 1, "choice_id": 1},
    )
    assert response.status_code == 404
