import io
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from app.constants.fields_of_study import NON_CPE
from app.db import SessionLocal
from app.main import app
from app.models.attempt import Attempt
from app.models.attempt_answer import AttemptAnswer
from app.models.choice import Choice
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.question import Question
from app.models.session import Session as SessionModel
from app.models.source import Source
from app.models.subject_matter_expert import SubjectMatterExpert
from app.models.user import User
from app.services import storage

client = TestClient(app)

SLUG_PREFIX = "test-admin-content"
ADMIN_EMAIL = "admin-content@example.com"
MEMBER_EMAIL = "member-content@example.com"
PASSWORD = "correct-horse-battery"

ADMIN_ROUTES = [
    ("GET", "/api/v1/admin/courses"),
    ("POST", "/api/v1/admin/courses"),
    ("GET", "/api/v1/admin/courses/999999"),
    ("PATCH", "/api/v1/admin/courses/999999"),
    ("DELETE", "/api/v1/admin/courses/999999"),
    ("POST", "/api/v1/admin/courses/999999/publish"),
    ("POST", "/api/v1/admin/courses/999999/unpublish"),
    ("POST", "/api/v1/admin/courses/999999/lessons"),
    ("POST", "/api/v1/admin/courses/999999/objectives"),
    ("PATCH", "/api/v1/admin/objectives/999999"),
    ("DELETE", "/api/v1/admin/objectives/999999"),
    ("POST", "/api/v1/admin/objectives/999999/move"),
    ("GET", "/api/v1/admin/lessons/999999"),
    ("PATCH", "/api/v1/admin/lessons/999999"),
    ("DELETE", "/api/v1/admin/lessons/999999"),
    ("POST", "/api/v1/admin/lessons/999999/move"),
    ("POST", "/api/v1/admin/lessons/999999/questions"),
    ("PATCH", "/api/v1/admin/questions/999999"),
    ("DELETE", "/api/v1/admin/questions/999999"),
    ("POST", "/api/v1/admin/questions/999999/move"),
    ("POST", "/api/v1/admin/questions/999999/choices"),
    ("PATCH", "/api/v1/admin/choices/999999"),
    ("DELETE", "/api/v1/admin/choices/999999"),
    ("POST", "/api/v1/admin/choices/999999/move"),
    ("POST", "/api/v1/admin/questions/999999/correct-choice"),
    ("GET", "/api/v1/admin/smes"),
    ("POST", "/api/v1/admin/smes"),
    ("GET", "/api/v1/admin/smes/999999"),
    ("PATCH", "/api/v1/admin/smes/999999"),
    ("DELETE", "/api/v1/admin/smes/999999"),
    ("POST", "/api/v1/admin/courses/999999/sources"),
    ("PATCH", "/api/v1/admin/sources/999999"),
    ("DELETE", "/api/v1/admin/sources/999999"),
    ("POST", "/api/v1/admin/sources/999999/move"),
    ("GET", "/api/v1/admin/courses/999999/credit"),
    ("POST", "/api/v1/admin/courses/999999/credit"),
]


@pytest.fixture(autouse=True)
def cleanup():
    client.cookies.clear()

    yield

    client.cookies.clear()
    db = SessionLocal()
    emails = [ADMIN_EMAIL, MEMBER_EMAIL]
    user_ids = select(User.id).where(User.email.in_(emails))
    course_ids = select(Course.id).where(Course.slug.like(f"{SLUG_PREFIX}%"))
    lesson_ids = select(Lesson.id).where(Lesson.course_id.in_(course_ids))
    question_ids = select(Question.id).where(Question.lesson_id.in_(lesson_ids))
    attempt_ids = select(Attempt.id).where(Attempt.course_id.in_(course_ids))
    db.execute(delete(AttemptAnswer).where(AttemptAnswer.attempt_id.in_(attempt_ids)))
    db.execute(delete(Attempt).where(Attempt.course_id.in_(course_ids)))
    db.execute(delete(Choice).where(Choice.question_id.in_(question_ids)))
    db.execute(delete(Question).where(Question.lesson_id.in_(lesson_ids)))
    db.execute(delete(Source).where(Source.course_id.in_(course_ids)))
    db.execute(delete(Course).where(Course.slug.like(f"{SLUG_PREFIX}%")))
    db.execute(delete(SubjectMatterExpert).where(SubjectMatterExpert.name.like(f"{SLUG_PREFIX}%")))
    db.execute(delete(SessionModel).where(SessionModel.user_id.in_(user_ids)))
    db.execute(delete(User).where(User.email.in_(emails)))
    db.commit()
    db.close()


def register_and_login(email, is_admin=False):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "display_name": "Test User"},
    )
    if is_admin:
        db = SessionLocal()
        user = db.execute(select(User).where(User.email == email)).scalar_one()
        user.is_admin = True
        db.commit()
        db.close()


def login_admin():
    register_and_login(ADMIN_EMAIL, is_admin=True)


def create_course(slug_suffix, **overrides):
    payload = {"title": f"Admin Test Course {slug_suffix}", "slug": f"{SLUG_PREFIX}-{slug_suffix}"}
    payload.update(overrides)
    response = client.post("/api/v1/admin/courses", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def create_lesson(course_id, slug_suffix, **overrides):
    payload = {"title": f"Admin Test Lesson {slug_suffix}", "slug": f"{SLUG_PREFIX}-lesson-{slug_suffix}"}
    payload.update(overrides)
    response = client.post(f"/api/v1/admin/courses/{course_id}/lessons", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def add_objective(course_id, text="Explain the objective."):
    response = client.post(f"/api/v1/admin/courses/{course_id}/objectives", json={"text": text})
    assert response.status_code == 201, response.text
    return response.json()


def add_complete_questions(lesson_id, count=1, objective_id=None):
    for i in range(count):
        question = client.post(
            f"/api/v1/admin/lessons/{lesson_id}/questions", json={"prompt": f"Question {i}"}
        )
        assert question.status_code == 201, question.text
        question_id = question.json()["id"]
        if objective_id is not None:
            update = client.patch(
                f"/api/v1/admin/questions/{question_id}", json={"objective_id": objective_id}
            )
            assert update.status_code == 200, update.text
        for j in range(4):
            choice = client.post(
                f"/api/v1/admin/questions/{question_id}/choices",
                json={"text": f"Choice {j}", "is_correct": j == 0},
            )
            assert choice.status_code == 201, choice.text


def add_question(lesson_id, prompt, kind="assessment", choice_count=4, objective_id=None, feedback=None):
    question = client.post(f"/api/v1/admin/lessons/{lesson_id}/questions", json={"prompt": prompt})
    assert question.status_code == 201, question.text
    question_id = question.json()["id"]
    updates = {}
    if kind != "assessment":
        updates["kind"] = kind
    if feedback is not None:
        updates["feedback"] = feedback
    if objective_id is not None:
        updates["objective_id"] = objective_id
    if updates:
        update = client.patch(f"/api/v1/admin/questions/{question_id}", json=updates)
        assert update.status_code == 200, update.text
    for j in range(choice_count):
        choice = client.post(
            f"/api/v1/admin/questions/{question_id}/choices",
            json={"text": f"Choice {j}", "is_correct": j == 0},
        )
        assert choice.status_code == 201, choice.text
    return question_id


def upload_video(slug, monkeypatch):
    monkeypatch.setattr(storage, "upload_fileobj", lambda fileobj, key, content_type: None)
    response = client.post(
        f"/api/v1/admin/lessons/{slug}/video",
        files={"file": ("video.mp4", io.BytesIO(b"data"), "video/mp4")},
    )
    assert response.status_code == 200, response.text


def create_sme(name_suffix, **overrides):
    payload = {
        "name": f"{SLUG_PREFIX} SME {name_suffix}",
        "credentials": "CPA, active, NH #12345",
    }
    payload.update(overrides)
    response = client.post("/api/v1/admin/smes", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def add_review_chain(course_id, slug_suffix, developer_overrides=None, reviewer_overrides=None):
    # Licensed CPA by default so an ordinary "complete course" helper doesn't
    # trip rules 6/7 for tests unrelated to the credential requirement; tests
    # that exercise those rules directly pass their own overrides.
    developer_overrides = {"is_licensed_cpa": True, **(developer_overrides or {})}
    developer = create_sme(f"{slug_suffix}-dev", **developer_overrides)
    reviewer = create_sme(f"{slug_suffix}-rev", **(reviewer_overrides or {}))
    response = client.patch(
        f"/api/v1/admin/courses/{course_id}",
        json={
            "developer_id": developer["id"],
            "reviewer_id": reviewer["id"],
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "review_notes": None,
            # The real Review panel PATCHes all five review fields together
            # in one request (ReviewPanel.jsx) - review_cycle must be
            # included here too so this helper would have caught the bug
            # where review_cycle wasn't excluded from the content_updated_at
            # bump, which silently staled every review the instant it saved.
            "review_cycle": "biennial",
        },
    )
    assert response.status_code == 200, response.text
    return developer, reviewer


@pytest.mark.parametrize("method,path", ADMIN_ROUTES)
def test_anonymous_gets_401(method, path):
    response = client.request(method, path, json={})
    assert response.status_code == 401


@pytest.mark.parametrize("method,path", ADMIN_ROUTES)
def test_non_admin_gets_403(method, path):
    register_and_login(MEMBER_EMAIL, is_admin=False)
    response = client.request(method, path, json={})
    assert response.status_code == 403


def test_create_course_is_unpublished():
    login_admin()
    course = create_course("create")
    assert course["is_published"] is False


def test_create_course_creates_first_lesson_in_the_same_transaction():
    login_admin()
    course = create_course("create-first-lesson")
    assert len(course["lessons"]) == 1
    lesson = course["lessons"][0]
    assert lesson["position"] == 1
    assert lesson["title"] == course["title"]


def test_create_lesson_adds_it_to_the_course_in_order():
    login_admin()
    course = create_course("lesson-order")
    auto_lesson = course["lessons"][0]
    lesson_a = create_lesson(course["id"], "a")
    lesson_b = create_lesson(course["id"], "b")

    detail = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    assert [lesson["id"] for lesson in detail["lessons"]] == [auto_lesson["id"], lesson_a["id"], lesson_b["id"]]
    assert [lesson["position"] for lesson in detail["lessons"]] == [1, 2, 3]


def test_reordering_lessons_produces_contiguous_positions():
    login_admin()
    course = create_course("lesson-reorder")
    l0 = course["lessons"][0]
    l1 = create_lesson(course["id"], "1")
    l2 = create_lesson(course["id"], "2")

    # l0, l1, l2 -> move l2 up -> l0, l2, l1 -> move l2 up again -> l2, l0, l1
    assert client.post(f"/api/v1/admin/lessons/{l2['id']}/move", json={"direction": "up"}).status_code == 204
    assert client.post(f"/api/v1/admin/lessons/{l2['id']}/move", json={"direction": "up"}).status_code == 204

    detail = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    positions = [(lesson["id"], lesson["position"]) for lesson in detail["lessons"]]
    assert [position for _, position in positions] == [1, 2, 3]
    assert [lesson_id for lesson_id, _ in positions] == [l2["id"], l0["id"], l1["id"]]


def test_update_course_round_trips_every_field_on_the_details_form_in_one_batch():
    login_admin()
    course = create_course("details-round-trip", description="original description")

    payload = {
        "title": "Renamed Title",
        "slug": f"{SLUG_PREFIX}-details-round-trip-renamed",
        "description": "Updated course description.",
        "retake_cooldown_minutes": 30,
        "max_attempts": 2,
        "program_level": "intermediate",
        "field_of_study": NON_CPE,
        "prerequisites": "Some prerequisite text.",
        "advance_preparation": "Some advance preparation text.",
    }
    response = client.patch(f"/api/v1/admin/courses/{course['id']}", json=payload)
    assert response.status_code == 200, response.text

    reloaded = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    for field, value in payload.items():
        assert reloaded[field] == value, f"{field} did not round-trip: {reloaded[field]!r} != {value!r}"


def test_publish_with_no_lessons_returns_422():
    # Course creation always creates lesson 1 now (feature 019a), so a
    # zero-lesson course can no longer be reached through the API. This
    # exercises validate_for_publish's defensive rule directly by deleting
    # the auto-created lesson underneath the course.
    login_admin()
    course = create_course("no-lessons")

    db = SessionLocal()
    db.execute(delete(Lesson).where(Lesson.course_id == course["id"]))
    db.commit()
    db.close()

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("at least one lesson" in error for error in errors)


def test_publish_with_a_lesson_missing_a_video_names_that_lesson():
    login_admin()
    course = create_course("missing-video")
    lesson = course["lessons"][0]
    add_complete_questions(lesson["id"], count=1)

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(lesson["title"] in error and "video" in error for error in errors)


def test_publish_with_a_lesson_missing_questions_names_that_lesson(monkeypatch):
    login_admin()
    course = create_course("missing-questions")
    lesson = course["lessons"][0]
    upload_video(lesson["slug"], monkeypatch)

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(lesson["title"] in error and "question" in error for error in errors)


def test_publish_with_missing_correct_choice_returns_422(monkeypatch):
    login_admin()
    course = create_course("no-correct-choice")
    lesson = course["lessons"][0]
    add_complete_questions(lesson["id"], count=1)
    upload_video(lesson["slug"], monkeypatch)

    detail = client.get(f"/api/v1/admin/lessons/{lesson['id']}").json()
    first_choice_id = detail["questions"][0]["choices"][0]["id"]
    unset = client.patch(f"/api/v1/admin/choices/{first_choice_id}", json={"is_correct": False})
    assert unset.status_code == 200

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("must have exactly one correct choice" in error for error in errors)


def test_dry_run_publish_reports_errors_without_publishing():
    login_admin()
    course = create_course("dry-run-incomplete")

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish?dry_run=true")
    assert response.status_code == 200
    errors = response.json()["errors"]
    assert any("video" in error for error in errors)

    detail = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    assert detail["is_published"] is False


def test_dry_run_publish_reports_no_errors_for_complete_course(monkeypatch):
    login_admin()
    course, _ = _make_publishable_course("dry-run-complete", monkeypatch)

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish?dry_run=true")
    assert response.status_code == 200
    assert response.json()["errors"] == []

    detail = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    assert detail["is_published"] is False


def test_publish_complete_course_succeeds_and_appears_in_public_list(monkeypatch):
    login_admin()
    course, _ = _make_publishable_course("complete", monkeypatch)

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 200
    assert response.json()["is_published"] is True

    public = client.get("/api/v1/courses")
    assert course["slug"] in [item["slug"] for item in public.json()]


def test_publishing_a_course_publishes_its_lessons_so_the_quiz_is_servable(monkeypatch):
    login_admin()
    course, lesson = _make_publishable_course("publish-cascades", monkeypatch)

    assert lesson["is_published"] is False

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 200
    assert response.json()["lessons"][0]["is_published"] is True

    detail = client.get(f"/api/v1/courses/{course['slug']}").json()
    assert len(detail["lessons"]) == 1

    quiz = client.get(f"/api/v1/courses/{course['slug']}/quiz")
    assert quiz.status_code == 200
    assert quiz.json()["question_count"] == 2


def test_unpublish_removes_from_public_list(monkeypatch):
    login_admin()
    course = create_course("unpublish", description="A course to unpublish.")
    lesson = course["lessons"][0]
    add_complete_questions(lesson["id"], count=1)
    upload_video(lesson["slug"], monkeypatch)
    add_objective(course["id"])
    add_review_chain(course["id"], "unpublish")
    client.post(f"/api/v1/admin/courses/{course['id']}/publish")

    response = client.post(f"/api/v1/admin/courses/{course['id']}/unpublish")
    assert response.status_code == 200
    assert response.json()["is_published"] is False

    public = client.get("/api/v1/courses")
    assert course["slug"] not in [item["slug"] for item in public.json()]


def test_setting_correct_choice_clears_previous():
    login_admin()
    course = create_course("correct-swap")
    lesson = create_lesson(course["id"], "correct-swap")
    question = client.post(
        f"/api/v1/admin/lessons/{lesson['id']}/questions", json={"prompt": "Which one?"}
    ).json()
    choice_a = client.post(
        f"/api/v1/admin/questions/{question['id']}/choices", json={"text": "A", "is_correct": True}
    ).json()
    choice_b = client.post(
        f"/api/v1/admin/questions/{question['id']}/choices", json={"text": "B"}
    ).json()

    response = client.post(
        f"/api/v1/admin/questions/{question['id']}/correct-choice", json={"choice_id": choice_b["id"]}
    )
    assert response.status_code == 204

    detail = client.get(f"/api/v1/admin/lessons/{lesson['id']}").json()
    choices = detail["questions"][0]["choices"]
    correct_ids = [choice["id"] for choice in choices if choice["is_correct"]]
    assert correct_ids == [choice_b["id"]]


def test_reordering_questions_produces_contiguous_positions():
    login_admin()
    course = create_course("question-reorder")
    lesson = create_lesson(course["id"], "question-reorder")
    q1 = client.post(f"/api/v1/admin/lessons/{lesson['id']}/questions", json={"prompt": "Q1"}).json()
    q2 = client.post(f"/api/v1/admin/lessons/{lesson['id']}/questions", json={"prompt": "Q2"}).json()
    q3 = client.post(f"/api/v1/admin/lessons/{lesson['id']}/questions", json={"prompt": "Q3"}).json()

    # Q1, Q2, Q3 -> move Q3 up -> Q1, Q3, Q2 -> move Q3 up again -> Q3, Q1, Q2
    assert client.post(f"/api/v1/admin/questions/{q3['id']}/move", json={"direction": "up"}).status_code == 204
    assert client.post(f"/api/v1/admin/questions/{q3['id']}/move", json={"direction": "up"}).status_code == 204

    detail = client.get(f"/api/v1/admin/lessons/{lesson['id']}").json()
    positions = [(question["id"], question["position"]) for question in detail["questions"]]
    assert [position for _, position in positions] == [1, 2, 3]
    assert [question_id for question_id, _ in positions] == [q3["id"], q1["id"], q2["id"]]


def test_delete_course_with_completed_attempt_returns_409():
    login_admin()
    course = create_course("delete-with-attempt")

    db = SessionLocal()
    db.add(
        Attempt(
            course_id=course["id"], score=4, passed=True, completed_at=datetime.now(timezone.utc)
        )
    )
    db.commit()
    db.close()

    response = client.delete(f"/api/v1/admin/courses/{course['id']}")
    assert response.status_code == 409


def test_delete_lesson_whose_course_has_a_completed_attempt_returns_409():
    login_admin()
    course = create_course("delete-lesson-with-attempt")
    lesson = create_lesson(course["id"], "delete-lesson-with-attempt")

    db = SessionLocal()
    db.add(
        Attempt(
            course_id=course["id"], score=4, passed=True, completed_at=datetime.now(timezone.utc)
        )
    )
    db.commit()
    db.close()

    response = client.delete(f"/api/v1/admin/lessons/{lesson['id']}")
    assert response.status_code == 409


def test_deleting_the_only_lesson_of_a_course_is_refused():
    login_admin()
    course = create_course("delete-only-lesson")
    lesson = course["lessons"][0]

    response = client.delete(f"/api/v1/admin/lessons/{lesson['id']}")
    assert response.status_code == 409
    assert "delete the course instead" in response.json()["detail"].lower()

    course_after = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    assert len(course_after["lessons"]) == 1
    lesson_after = client.get(f"/api/v1/admin/lessons/{lesson['id']}")
    assert lesson_after.status_code == 200


def test_deleting_one_of_two_lessons_succeeds():
    login_admin()
    course = create_course("delete-one-of-two")
    second = create_lesson(course["id"], "second")

    response = client.delete(f"/api/v1/admin/lessons/{second['id']}")
    assert response.status_code == 204

    course_after = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    assert len(course_after["lessons"]) == 1
    assert course_after["lessons"][0]["id"] == course["lessons"][0]["id"]


# --- learning objectives, program metadata (feature 020) --------------------


def _make_publishable_course(slug_suffix, monkeypatch, **course_overrides):
    course = create_course(slug_suffix, description="A complete test course.")
    if course_overrides:
        response = client.patch(f"/api/v1/admin/courses/{course['id']}", json=course_overrides)
        assert response.status_code == 200, response.text
        course = response.json()
    lesson = course["lessons"][0]
    # Feature 023a: 6.01.2 requires the assessment to measure 75% of the
    # course's objectives - with exactly one objective, every assessment
    # question must be tagged to it.
    objective = add_objective(course["id"])
    # Feature 023: 6.01.2 requires at least 2 qualified assessment questions
    # even at the smallest (0.2 credit) tier - one question is no longer a
    # publishable course. add_complete_questions defaults every question to
    # kind='assessment' and 4 choices, clearing MIN_CHOICES_ASSESSMENT too.
    add_complete_questions(lesson["id"], count=2, objective_id=objective["id"])
    upload_video(lesson["slug"], monkeypatch)
    # Feature 022: enough runtime for credit >= 0.2, the minimum awardable
    # increment (7.01). 600s A/V + 2 questions x 1.85 min = 13.7 min / 50 =
    # 0.274 -> floor(1.37)/5 -> 0.2 credit, with margin from both the 0.2 and
    # 0.4 tier boundaries. At 0.2 credit, 5.01.2.1 requires 0 review
    # questions and 6.01.2 requires 2 assessment questions - exactly what's
    # seeded above.
    response = client.patch(f"/api/v1/admin/lessons/{lesson['id']}", json={"duration_seconds": 600})
    assert response.status_code == 200, response.text
    add_review_chain(course["id"], slug_suffix)
    response = client.post(f"/api/v1/admin/courses/{course['id']}/credit")
    assert response.status_code == 200, response.text
    course = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    return course, lesson


def test_create_course_defaults_to_basic_level_and_non_cpe_field():
    login_admin()
    course = create_course("defaults")
    assert course["program_level"] == "basic"
    assert course["field_of_study"] == NON_CPE
    assert course["learning_objectives"] == []


def test_publish_with_no_objectives_returns_422(monkeypatch):
    login_admin()
    course = create_course("no-objectives")
    lesson = course["lessons"][0]
    add_complete_questions(lesson["id"], count=1)
    upload_video(lesson["slug"], monkeypatch)

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("learning objective" in error for error in errors)


def test_publish_intermediate_course_with_empty_prerequisites_returns_422(monkeypatch):
    login_admin()
    course, _ = _make_publishable_course(
        "intermediate-missing-prereqs", monkeypatch, program_level="intermediate"
    )

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("Prerequisites" in error for error in errors)
    assert any("Advance preparation" in error for error in errors)


def test_publish_basic_course_with_empty_prerequisites_succeeds(monkeypatch):
    login_admin()
    course, _ = _make_publishable_course("basic-empty-prereqs", monkeypatch, program_level="basic")

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 200


def test_publish_intermediate_course_with_prerequisites_succeeds(monkeypatch):
    login_admin()
    course, _ = _make_publishable_course(
        "intermediate-complete",
        monkeypatch,
        program_level="intermediate",
        prerequisites="Two years of general accounting experience.",
        advance_preparation="Review the attached memo before the course.",
    )

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 200


def test_unknown_field_of_study_rejected_by_constraint():
    login_admin()
    course = create_course("bad-field-of-study")

    db = SessionLocal()
    row = db.get(Course, course["id"])
    row.field_of_study = "Not A Real Field"
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    db.close()


def test_unknown_program_level_rejected_by_constraint():
    login_admin()
    course = create_course("bad-program-level")

    db = SessionLocal()
    row = db.get(Course, course["id"])
    row.program_level = "expert"
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    db.close()


def test_objectives_come_back_in_position_order_and_reorder_correctly():
    login_admin()
    course = create_course("objective-order")
    o1 = add_objective(course["id"], "First objective")
    o2 = add_objective(course["id"], "Second objective")
    o3 = add_objective(course["id"], "Third objective")

    detail = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    assert [o["id"] for o in detail["learning_objectives"]] == [o1["id"], o2["id"], o3["id"]]
    assert [o["position"] for o in detail["learning_objectives"]] == [1, 2, 3]

    # o1, o2, o3 -> move o3 up -> o1, o3, o2 -> move o3 up again -> o3, o1, o2
    assert client.post(f"/api/v1/admin/objectives/{o3['id']}/move", json={"direction": "up"}).status_code == 204
    assert client.post(f"/api/v1/admin/objectives/{o3['id']}/move", json={"direction": "up"}).status_code == 204

    detail = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    positions = [(o["id"], o["position"]) for o in detail["learning_objectives"]]
    assert [position for _, position in positions] == [1, 2, 3]
    assert [objective_id for objective_id, _ in positions] == [o3["id"], o1["id"], o2["id"]]


def test_deleting_an_objective_renumbers_the_rest():
    login_admin()
    course = create_course("objective-delete")
    o1 = add_objective(course["id"], "First")
    o2 = add_objective(course["id"], "Second")
    o3 = add_objective(course["id"], "Third")

    assert client.delete(f"/api/v1/admin/objectives/{o2['id']}").status_code == 204

    detail = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    positions = [(o["id"], o["position"]) for o in detail["learning_objectives"]]
    assert positions == [(o1["id"], 1), (o3["id"], 2)]


def test_editing_an_objective_updates_its_text():
    login_admin()
    course = create_course("objective-edit")
    objective = add_objective(course["id"], "Original text")

    response = client.patch(f"/api/v1/admin/objectives/{objective['id']}", json={"text": "Updated text"})
    assert response.status_code == 200
    assert response.json()["text"] == "Updated text"


def test_public_course_payload_carries_program_metadata(monkeypatch):
    login_admin()
    course, _ = _make_publishable_course(
        "public-metadata",
        monkeypatch,
        program_level="intermediate",
        field_of_study="Auditing",
        prerequisites="Two years of experience.",
        advance_preparation="Read chapter one.",
    )
    client.post(f"/api/v1/admin/courses/{course['id']}/publish")

    response = client.get(f"/api/v1/courses/{course['slug']}")
    assert response.status_code == 200
    body = response.json()
    assert body["program_level"] == "intermediate"
    assert body["field_of_study"] == "Auditing"
    assert body["prerequisites"] == "Two years of experience."
    assert body["advance_preparation"] == "Read chapter one."
    assert [o["text"] for o in body["learning_objectives"]] == ["Explain the objective."]


def test_public_course_payload_exposes_none_prerequisites_for_basic_course(monkeypatch):
    login_admin()
    course, _ = _make_publishable_course("public-metadata-basic", monkeypatch, program_level="basic")
    client.post(f"/api/v1/admin/courses/{course['id']}/publish")

    response = client.get(f"/api/v1/courses/{course['slug']}")
    body = response.json()
    assert body["prerequisites"] is None
    assert body["advance_preparation"] is None


def test_meta_fields_of_study_lists_all_values():
    response = client.get("/api/v1/meta/fields-of-study")
    assert response.status_code == 200
    body = response.json()
    assert body["non_cpe"] == NON_CPE
    technical_names = [field["name"] for field in body["technical"]]
    assert "Accounting" in technical_names
    assert {"name": "Accounting", "credential_tag": "cpa"} in body["technical"]
    assert {"name": "Taxes", "credential_tag": "tax"} in body["technical"]
    non_technical_names = [field["name"] for field in body["non_technical"]]
    assert "Behavioral Ethics" in non_technical_names


def test_meta_program_levels_lists_all_five():
    response = client.get("/api/v1/meta/program-levels")
    assert response.status_code == 200
    assert response.json()["levels"] == ["basic", "intermediate", "advanced", "update", "overview"]


# --- development and review chain (feature 021) ------------------------------


def test_publish_with_no_developer_is_refused_and_names_it(monkeypatch):
    login_admin()
    course, lesson = _make_publishable_course("no-developer", monkeypatch)
    # Clear the developer that _make_publishable_course set, keeping the
    # reviewer and review date, to isolate rule 1.
    client.patch(f"/api/v1/admin/courses/{course['id']}", json={"developer_id": None})

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("developer" in error.lower() for error in errors)


def test_setting_same_expert_as_both_developer_and_reviewer_is_refused_by_the_api():
    login_admin()
    course = create_course("same-person")
    sme = create_sme("same-person", is_licensed_cpa=True)

    response = client.patch(
        f"/api/v1/admin/courses/{course['id']}",
        json={"developer_id": sme["id"], "reviewer_id": sme["id"]},
    )
    assert response.status_code == 409
    assert "different people" in response.json()["detail"]


def test_setting_same_expert_as_both_via_db_violates_check_constraint():
    login_admin()
    course = create_course("same-person-db")
    sme = create_sme("same-person-db", is_licensed_cpa=True)

    db = SessionLocal()
    row = db.get(Course, course["id"])
    row.developer_id = sme["id"]
    row.reviewer_id = sme["id"]
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    db.close()


def test_publish_with_review_older_than_content_edit_is_refused(monkeypatch):
    login_admin()
    course, lesson = _make_publishable_course("stale-review", monkeypatch)

    # The review recorded by _make_publishable_course now predates this edit.
    response = client.patch(f"/api/v1/admin/lessons/{lesson['id']}", json={"description": "Edited after review."})
    assert response.status_code == 200

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("changed since it was reviewed" in error for error in errors)


def test_recording_a_review_does_not_change_content_updated_at(monkeypatch):
    login_admin()
    course = create_course("review-no-touch")
    lesson = course["lessons"][0]
    add_complete_questions(lesson["id"], count=1)
    upload_video(lesson["slug"], monkeypatch)
    add_objective(course["id"])
    before = client.get(f"/api/v1/admin/courses/{course['id']}").json()["content_updated_at"]

    add_review_chain(course["id"], "review-no-touch")

    after = client.get(f"/api/v1/admin/courses/{course['id']}").json()["content_updated_at"]
    assert after == before

    # Feature 022: the seven credit_* fields get the same REVIEW_CHAIN_FIELDS
    # exclusion for the same reason - storing a computed credit must not
    # itself make the credit stale. Extended per current-feature.md, which
    # notes 021's version of this test only covered three of five review
    # fields the first time and missed a real bug - PATCH all seven here.
    response = client.patch(
        f"/api/v1/admin/courses/{course['id']}",
        json={
            "credit_award": "0.4",
            "credit_raw_minutes": "20.00",
            "credit_word_count": 0,
            "credit_av_seconds": 600,
            "credit_question_count": 5,
            "credit_formula_version": "2026-7.02.6",
            "credit_computed_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert response.status_code == 200, response.text

    after_credit = client.get(f"/api/v1/admin/courses/{course['id']}").json()["content_updated_at"]
    assert after_credit == before


def test_editing_a_question_changes_content_updated_at(monkeypatch):
    login_admin()
    course, lesson = _make_publishable_course("question-touch", monkeypatch)
    before = client.get(f"/api/v1/admin/courses/{course['id']}").json()["content_updated_at"]

    question_id = client.get(f"/api/v1/admin/lessons/{lesson['id']}").json()["questions"][0]["id"]
    response = client.patch(f"/api/v1/admin/questions/{question_id}", json={"prompt": "Updated prompt?"})
    assert response.status_code == 200

    after = client.get(f"/api/v1/admin/courses/{course['id']}").json()["content_updated_at"]
    assert after > before


def test_adding_a_source_does_not_change_content_updated_at(monkeypatch):
    login_admin()
    course, lesson = _make_publishable_course("source-no-touch", monkeypatch)
    before = client.get(f"/api/v1/admin/courses/{course['id']}").json()["content_updated_at"]

    response = client.post(
        f"/api/v1/admin/courses/{course['id']}/sources",
        json={"citation": "NASBA 2026 Statement on Standards", "url": None, "retrieved_on": None},
    )
    assert response.status_code == 201, response.text

    after = client.get(f"/api/v1/admin/courses/{course['id']}").json()["content_updated_at"]
    assert after == before

    # Publish still succeeds - a source does not make the existing review stale.
    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 200, response.text


def test_accounting_course_with_no_licensed_cpa_is_refused(monkeypatch):
    login_admin()
    course, lesson = _make_publishable_course(
        "accounting-no-cpa", monkeypatch, field_of_study="Accounting"
    )
    # _make_publishable_course's developer is a CPA by default; strip it so
    # neither side of the chain carries the credential. Editing the SME
    # record itself is not a course-content mutation, so the existing review
    # stays fresh.
    developer_id = client.get(f"/api/v1/admin/courses/{course['id']}").json()["developer_id"]
    client.patch(f"/api/v1/admin/smes/{developer_id}", json={"is_licensed_cpa": False})

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("licensed CPA" in error for error in errors)


def test_taxes_course_with_enrolled_agent_as_reviewer_publishes(monkeypatch):
    login_admin()
    course = create_course("taxes-enrolled-agent", description="A complete test course.")
    lesson = course["lessons"][0]
    objective = add_objective(course["id"])
    add_complete_questions(lesson["id"], count=2, objective_id=objective["id"])
    upload_video(lesson["slug"], monkeypatch)
    client.patch(f"/api/v1/admin/courses/{course['id']}", json={"field_of_study": "Taxes"})
    client.patch(f"/api/v1/admin/lessons/{lesson['id']}", json={"duration_seconds": 600})

    developer = create_sme("taxes-ea-dev")
    reviewer = create_sme("taxes-ea-rev", is_enrolled_agent=True)
    response = client.patch(
        f"/api/v1/admin/courses/{course['id']}",
        json={
            "developer_id": developer["id"],
            "reviewer_id": reviewer["id"],
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert response.status_code == 200

    response = client.post(f"/api/v1/admin/courses/{course['id']}/credit")
    assert response.status_code == 200, response.text

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 200, response.text


def test_non_technical_course_is_unaffected_by_credential_rules(monkeypatch):
    login_admin()
    course, lesson = _make_publishable_course(
        "non-technical", monkeypatch, field_of_study="Behavioral Ethics"
    )
    developer_id = client.get(f"/api/v1/admin/courses/{course['id']}").json()["developer_id"]
    client.patch(f"/api/v1/admin/smes/{developer_id}", json={"is_licensed_cpa": False})

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 200, response.text


def test_public_course_payload_carries_review_date_and_expert_names(monkeypatch):
    login_admin()
    course, lesson = _make_publishable_course("public-review", monkeypatch)
    publish = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert publish.status_code == 200, publish.text
    admin_course = client.get(f"/api/v1/admin/courses/{course['id']}").json()

    response = client.get(f"/api/v1/courses/{course['slug']}")
    assert response.status_code == 200
    body = response.json()
    assert body["reviewed_at"] is not None
    assert body["developer"]["name"] == admin_course["developer"]["name"]
    assert body["developer"]["credentials"] == admin_course["developer"]["credentials"]
    assert body["reviewer"]["name"] == admin_course["reviewer"]["name"]
    assert "bio" not in body["developer"]
    assert "affiliation" not in body["developer"]


def test_sources_come_back_in_position_order_and_reorder_correctly():
    login_admin()
    course = create_course("sources-order")

    def add_source(citation):
        response = client.post(
            f"/api/v1/admin/courses/{course['id']}/sources", json={"citation": citation}
        )
        assert response.status_code == 201, response.text
        return response.json()

    s1 = add_source("Source one")
    s2 = add_source("Source two")
    s3 = add_source("Source three")

    detail = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    assert [s["citation"] for s in detail["sources"]] == ["Source one", "Source two", "Source three"]
    assert [s["position"] for s in detail["sources"]] == [1, 2, 3]

    # s3, s3 up, s3 up -> s3, s1, s2
    assert client.post(f"/api/v1/admin/sources/{s3['id']}/move", json={"direction": "up"}).status_code == 204
    assert client.post(f"/api/v1/admin/sources/{s3['id']}/move", json={"direction": "up"}).status_code == 204

    detail = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    assert [s["id"] for s in detail["sources"]] == [s3["id"], s1["id"], s2["id"]]
    assert [s["position"] for s in detail["sources"]] == [1, 2, 3]

    delete_response = client.delete(f"/api/v1/admin/sources/{s1['id']}")
    assert delete_response.status_code == 204
    detail = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    assert [s["id"] for s in detail["sources"]] == [s3["id"], s2["id"]]
    assert [s["position"] for s in detail["sources"]] == [1, 2]


def test_sme_crud():
    login_admin()
    created = client.post(
        "/api/v1/admin/smes",
        json={
            "name": f"{SLUG_PREFIX} SME crud",
            "credentials": "CPA, active, CA #99999",
            "affiliation": "Acme Advisory",
            "is_licensed_cpa": True,
        },
    )
    assert created.status_code == 201, created.text
    sme = created.json()
    assert sme["is_licensed_cpa"] is True
    assert sme["is_tax_attorney"] is False

    fetched = client.get(f"/api/v1/admin/smes/{sme['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["affiliation"] == "Acme Advisory"

    updated = client.patch(f"/api/v1/admin/smes/{sme['id']}", json={"affiliation": "New Firm"})
    assert updated.status_code == 200
    assert updated.json()["affiliation"] == "New Firm"

    listed = client.get("/api/v1/admin/smes")
    assert listed.status_code == 200
    assert sme["id"] in [item["id"] for item in listed.json()]

    deleted = client.delete(f"/api/v1/admin/smes/{sme['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/admin/smes/{sme['id']}").status_code == 404


def test_deleting_an_sme_in_use_as_developer_or_reviewer_is_refused(monkeypatch):
    login_admin()
    course, lesson = _make_publishable_course("sme-in-use", monkeypatch)
    developer_id = client.get(f"/api/v1/admin/courses/{course['id']}").json()["developer_id"]

    response = client.delete(f"/api/v1/admin/smes/{developer_id}")
    assert response.status_code == 409


# --- feature 023: review/assessment question types and floors --------------


def test_publish_refuses_at_0_4_credit_naming_both_review_and_assessment_shortfalls(monkeypatch):
    login_admin()
    course = create_course("floor-both-shortfalls")
    lesson = course["lessons"][0]
    # Two review questions with exactly two choices don't count toward the
    # 0.4-credit review floor of 1 (5.01.2.1 - "true or false" style
    # questions don't count); two assessment questions fall short of the
    # 0.4-credit assessment floor of 3 (6.01.2).
    add_question(lesson["id"], "Review one?", kind="review", choice_count=2)
    add_question(lesson["id"], "Review two?", kind="review", choice_count=2)
    add_question(lesson["id"], "Assessment one?", kind="assessment", choice_count=4)
    add_question(lesson["id"], "Assessment two?", kind="assessment", choice_count=4)
    upload_video(lesson["slug"], monkeypatch)
    # (1000/60 + 4*1.85) / 50 = 0.481 -> floor(2.405)/5 -> 0.4 credit.
    client.patch(f"/api/v1/admin/lessons/{lesson['id']}", json={"duration_seconds": 1000})
    add_objective(course["id"])
    add_review_chain(course["id"], "floor-both-shortfalls")
    credit = client.post(f"/api/v1/admin/courses/{course['id']}/credit")
    assert credit.status_code == 200, credit.text
    award = Decimal(str(client.get(f"/api/v1/admin/courses/{course['id']}").json()["credit_award"]))
    assert award == Decimal("0.4")

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("review question(s)" in error and "it has 0" in error for error in errors)
    assert any("qualified assessment question(s)" in error and "it has 2" in error for error in errors)


def test_publish_with_a_two_choice_assessment_question_is_refused(monkeypatch):
    login_admin()
    course = create_course("two-choice-assessment")
    lesson = course["lessons"][0]
    add_question(lesson["id"], "Forced choice?", kind="assessment", choice_count=2)
    upload_video(lesson["slug"], monkeypatch)

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(
        "at least 3 choices" in error and "qualified assessment" in error for error in errors
    )


def test_two_choice_review_question_is_allowed_but_does_not_count_toward_the_floor(monkeypatch):
    login_admin()
    course = create_course("uncounted-review")
    lesson = course["lessons"][0]
    add_question(lesson["id"], "True or false review?", kind="review", choice_count=2)
    add_question(lesson["id"], "Assessment one?", kind="assessment", choice_count=4)
    add_question(lesson["id"], "Assessment two?", kind="assessment", choice_count=4)
    add_question(lesson["id"], "Assessment three?", kind="assessment", choice_count=4)
    upload_video(lesson["slug"], monkeypatch)
    # Same arithmetic as the both-shortfalls test above: 0.4 credit, which
    # requires 1 review question and 3 assessment questions.
    client.patch(f"/api/v1/admin/lessons/{lesson['id']}", json={"duration_seconds": 1000})
    add_objective(course["id"])
    add_review_chain(course["id"], "uncounted-review")
    credit = client.post(f"/api/v1/admin/courses/{course['id']}/credit")
    assert credit.status_code == 200, credit.text

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    # The two-choice review question is valid content (>= the global
    # MIN_CHOICES_PER_QUESTION floor of 2) - it just isn't counted, so the
    # only failure is the review floor itself, not a choice-count error and
    # not the (already-satisfied) assessment floor.
    assert any("review question(s)" in error and "it has 0" in error for error in errors)
    assert not any("qualified assessment question(s)" in error for error in errors)
    assert not any("needs at least" in error and "choices" in error for error in errors)


def test_publish_refuses_exact_duplicate_prompt_between_review_and_assessment(monkeypatch):
    login_admin()
    course = create_course("duplicate-prompt")
    lesson = course["lessons"][0]
    add_question(lesson["id"], "  What is  Recognition?  ", kind="review", choice_count=4)
    add_question(lesson["id"], "what is recognition?", kind="assessment", choice_count=4)
    add_question(lesson["id"], "Second assessment question?", kind="assessment", choice_count=4)
    add_question(lesson["id"], "Third assessment question?", kind="assessment", choice_count=4)
    upload_video(lesson["slug"], monkeypatch)
    client.patch(f"/api/v1/admin/lessons/{lesson['id']}", json={"duration_seconds": 1000})
    add_objective(course["id"])
    add_review_chain(course["id"], "duplicate-prompt")
    credit = client.post(f"/api/v1/admin/courses/{course['id']}/credit")
    assert credit.status_code == 200, credit.text

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(
        "exact same prompt" in error and "recall of information" in error and "exact matches only" in error
        for error in errors
    )


# --- feature 023a: feedback, objective coverage, and assessment integrity --


# The hazardous waste course: 5 lessons, 5 course-level objectives (one per
# lesson), 4/3/3/3/2 questions per lesson (15 total - position 1 in every
# lesson is the review question, the rest assessment - 5 review, 10
# assessment). Assessment questions tag objectives 1,1,1 / 2,2 / 3,3 / 4,4 /
# 5 - every objective covered, 100% against 6.01.2's 75% floor.
HAZWASTE_QUESTIONS_PER_LESSON = [4, 3, 3, 3, 2]
HAZWASTE_ASSESSMENT_OBJECTIVES = [1, 1, 1, 2, 2, 3, 3, 4, 4, 5]


def _build_hazardous_waste_course(slug_suffix, monkeypatch, av_seconds_per_lesson):
    login_admin()
    course = create_course(slug_suffix, description="Hazardous waste handling and disposal.")
    objectives = [add_objective(course["id"], f"Objective {n}") for n in range(1, 6)]

    lessons = [course["lessons"][0]]
    for i in range(2, 6):
        lessons.append(create_lesson(course["id"], f"{slug_suffix}-{i}"))

    remaining_objective_numbers = list(HAZWASTE_ASSESSMENT_OBJECTIVES)
    for lesson, question_count in zip(lessons, HAZWASTE_QUESTIONS_PER_LESSON):
        upload_video(lesson["slug"], monkeypatch)
        response = client.patch(
            f"/api/v1/admin/lessons/{lesson['id']}",
            json={"duration_seconds": av_seconds_per_lesson, "av_is_additional_learning": True},
        )
        assert response.status_code == 200, response.text

        add_question(
            lesson["id"],
            f"Review question for lesson {lesson['position']}?",
            kind="review",
            feedback="Review feedback text.",
        )
        for position_in_lesson in range(2, question_count + 1):
            objective_number = remaining_objective_numbers.pop(0)
            add_question(
                lesson["id"],
                f"Assessment question {position_in_lesson} for lesson {lesson['position']}?",
                kind="assessment",
                objective_id=objectives[objective_number - 1]["id"],
                feedback="Assessment feedback text.",
            )

    add_review_chain(course["id"], slug_suffix)
    credit = client.post(f"/api/v1/admin/courses/{course['id']}/credit")
    assert credit.status_code == 200, credit.text
    course = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    return course, objectives


# 27 minutes of video -> 1.0 credit; 33 minutes -> 1.2 credit (the script/
# video pipeline's measured range for this fixture's five segments, against
# a fixed 27.75-minute term from 15 questions x 1.85). One test, two
# parameters, so the chart's above-one-credit addition rule is exercised,
# not just its base case - current-feature.md's own worked example: 1.2
# credit needs 5+2=7 assessment questions and 3+0=3 review questions, both
# comfortably cleared by this fixture's 10 and 5.
@pytest.mark.parametrize(
    "seconds_per_lesson,expected_credit",
    [(324, "1.0"), (396, "1.2")],
)
def test_hazardous_waste_fixture_publishes_at_both_credit_boundaries(monkeypatch, seconds_per_lesson, expected_credit):
    course, _ = _build_hazardous_waste_course(
        f"hazwaste-{expected_credit.replace('.', '-')}", monkeypatch, seconds_per_lesson
    )
    assert Decimal(str(course["credit_award"])) == Decimal(expected_credit)

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 200, response.text


def test_publish_at_0_4_credit_with_exactly_the_floor_counts_succeeds(monkeypatch):
    login_admin()
    course = create_course("floor-exact-0-4", description="A complete test course.")
    lesson = course["lessons"][0]
    objective = add_objective(course["id"])
    add_question(lesson["id"], "Review one?", kind="review", feedback="Feedback text.")
    for i in range(3):
        add_question(lesson["id"], f"Assessment {i}?", kind="assessment", objective_id=objective["id"])
    upload_video(lesson["slug"], monkeypatch)
    client.patch(f"/api/v1/admin/lessons/{lesson['id']}", json={"duration_seconds": 1000})
    add_review_chain(course["id"], "floor-exact-0-4")
    credit = client.post(f"/api/v1/admin/courses/{course['id']}/credit")
    assert credit.status_code == 200, credit.text
    award = Decimal(str(client.get(f"/api/v1/admin/courses/{course['id']}").json()["credit_award"]))
    assert award == Decimal("0.4")

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 200, response.text


def test_publish_at_1_2_credit_with_six_assessment_questions_is_refused_naming_seven(monkeypatch):
    login_admin()
    course = create_course("floor-1-2-shortfall", description="A complete test course.")
    lesson = course["lessons"][0]
    objective = add_objective(course["id"])
    for i in range(3):
        add_question(lesson["id"], f"Review {i}?", kind="review", feedback="Feedback text.")
    for i in range(6):
        add_question(lesson["id"], f"Assessment {i}?", kind="assessment", objective_id=objective["id"])
    upload_video(lesson["slug"], monkeypatch)
    # (2646/60 + 9*1.85) / 50 = 1.215 -> floor(6.075)/5 -> 1.2 credit.
    client.patch(f"/api/v1/admin/lessons/{lesson['id']}", json={"duration_seconds": 2646})
    add_review_chain(course["id"], "floor-1-2-shortfall")
    credit = client.post(f"/api/v1/admin/courses/{course['id']}/credit")
    assert credit.status_code == 200, credit.text
    award = Decimal(str(client.get(f"/api/v1/admin/courses/{course['id']}").json()["credit_award"]))
    assert award == Decimal("1.2")

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(
        "qualified assessment question(s)" in error and "at least 7" in error and "it has 6" in error
        for error in errors
    )


def test_dropping_the_objective_5_question_still_publishes_at_80_percent_coverage(monkeypatch):
    course, objectives = _build_hazardous_waste_course("coverage-80", monkeypatch, 324)

    lesson5 = course["lessons"][4]
    detail = client.get(f"/api/v1/admin/lessons/{lesson5['id']}").json()
    obj5_question = next(q for q in detail["questions"] if q["objective_id"] == objectives[4]["id"])
    delete = client.delete(f"/api/v1/admin/questions/{obj5_question['id']}")
    assert delete.status_code == 204

    # Dropping a question is a content edit like any other - it stales both
    # the review and the computed credit (021, 022), unrelated to this
    # test's actual point (coverage). Clear both the same way an author
    # would: recompute credit, then re-record the review.
    credit = client.post(f"/api/v1/admin/courses/{course['id']}/credit")
    assert credit.status_code == 200, credit.text
    review = client.patch(
        f"/api/v1/admin/courses/{course['id']}", json={"reviewed_at": datetime.now(timezone.utc).isoformat()}
    )
    assert review.status_code == 200, review.text

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 200, response.text


def test_dropping_objective_4_and_5_questions_drops_coverage_to_60_percent_and_names_both(monkeypatch):
    course, objectives = _build_hazardous_waste_course("coverage-60", monkeypatch, 324)

    all_questions = []
    for lesson in course["lessons"]:
        all_questions.extend(client.get(f"/api/v1/admin/lessons/{lesson['id']}").json()["questions"])
    for objective in (objectives[3], objectives[4]):
        for question in [q for q in all_questions if q["objective_id"] == objective["id"]]:
            delete = client.delete(f"/api/v1/admin/questions/{question['id']}")
            assert delete.status_code == 204

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(
        "Objective 4" in error and "Objective 5" in error and "6.01.2" in error for error in errors
    )


def test_publish_with_a_review_question_missing_feedback_is_refused(monkeypatch):
    login_admin()
    course = create_course("review-no-feedback", description="A complete test course.")
    lesson = course["lessons"][0]
    objective = add_objective(course["id"])
    add_question(lesson["id"], "Review with no feedback?", kind="review", choice_count=4)
    for i in range(2):
        add_question(lesson["id"], f"Assessment {i}?", kind="assessment", objective_id=objective["id"])
    upload_video(lesson["slug"], monkeypatch)
    client.patch(f"/api/v1/admin/lessons/{lesson['id']}", json={"duration_seconds": 600})
    add_review_chain(course["id"], "review-no-feedback")
    credit = client.post(f"/api/v1/admin/courses/{course['id']}/credit")
    assert credit.status_code == 200, credit.text

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("needs feedback" in error and "5.01.2.2" in error for error in errors)


def test_deleting_an_objective_untags_its_questions_and_coverage_failure_persists(monkeypatch):
    login_admin()
    course = create_course("delete-objective-coverage", description="A complete test course.")
    lesson = course["lessons"][0]
    objective_a = add_objective(course["id"], "Objective A")
    add_objective(course["id"], "Objective B")
    add_objective(course["id"], "Objective C")
    tagged_question_id = add_question(
        lesson["id"], "Tagged to A?", kind="assessment", objective_id=objective_a["id"]
    )
    add_question(lesson["id"], "Untagged assessment?", kind="assessment")
    upload_video(lesson["slug"], monkeypatch)
    client.patch(f"/api/v1/admin/lessons/{lesson['id']}", json={"duration_seconds": 600})
    add_review_chain(course["id"], "delete-objective-coverage")
    credit = client.post(f"/api/v1/admin/courses/{course['id']}/credit")
    assert credit.status_code == 200, credit.text

    # 1 of 3 objectives covered before deletion - already below 75%.
    before = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert before.status_code == 422
    assert any("6.01.2" in error for error in before.json()["detail"])

    delete = client.delete(f"/api/v1/admin/objectives/{objective_a['id']}")
    assert delete.status_code == 204

    questions = client.get(f"/api/v1/admin/lessons/{lesson['id']}").json()["questions"]
    tagged_question = next(q for q in questions if q["id"] == tagged_question_id)
    assert tagged_question["objective_id"] is None

    after = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert after.status_code == 422
    errors = after.json()["detail"]
    assert any("Objective B" in error and "Objective C" in error and "6.01.2" in error for error in errors)


def test_editing_feedback_and_retagging_objective_each_bump_content_updated_at(monkeypatch):
    login_admin()
    course, lesson = _make_publishable_course("touch-feedback-objective", monkeypatch)
    question_id = client.get(f"/api/v1/admin/lessons/{lesson['id']}").json()["questions"][0]["id"]
    second_objective = add_objective(course["id"], "A second objective")

    before = client.get(f"/api/v1/admin/courses/{course['id']}").json()["content_updated_at"]
    response = client.patch(f"/api/v1/admin/questions/{question_id}", json={"feedback": "New feedback."})
    assert response.status_code == 200, response.text
    after_feedback = client.get(f"/api/v1/admin/courses/{course['id']}").json()["content_updated_at"]
    assert after_feedback > before

    response = client.patch(
        f"/api/v1/admin/questions/{question_id}", json={"objective_id": second_objective["id"]}
    )
    assert response.status_code == 200, response.text
    after_retag = client.get(f"/api/v1/admin/courses/{course['id']}").json()["content_updated_at"]
    assert after_retag > after_feedback
