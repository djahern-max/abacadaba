import io
from datetime import datetime, timezone

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
    db.execute(delete(Course).where(Course.slug.like(f"{SLUG_PREFIX}%")))
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


def add_complete_questions(lesson_id, count=1):
    for i in range(count):
        question = client.post(
            f"/api/v1/admin/lessons/{lesson_id}/questions", json={"prompt": f"Question {i}"}
        )
        assert question.status_code == 201, question.text
        question_id = question.json()["id"]
        for j in range(4):
            choice = client.post(
                f"/api/v1/admin/questions/{question_id}/choices",
                json={"text": f"Choice {j}", "is_correct": j == 0},
            )
            assert choice.status_code == 201, choice.text


def upload_video(slug, monkeypatch):
    monkeypatch.setattr(storage, "upload_fileobj", lambda fileobj, key, content_type: None)
    response = client.post(
        f"/api/v1/admin/lessons/{slug}/video",
        files={"file": ("video.mp4", io.BytesIO(b"data"), "video/mp4")},
    )
    assert response.status_code == 200, response.text


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
    assert course["lessons"] == []


def test_create_lesson_adds_it_to_the_course_in_order():
    login_admin()
    course = create_course("lesson-order")
    lesson_a = create_lesson(course["id"], "a")
    lesson_b = create_lesson(course["id"], "b")

    detail = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    assert [lesson["id"] for lesson in detail["lessons"]] == [lesson_a["id"], lesson_b["id"]]
    assert [lesson["position"] for lesson in detail["lessons"]] == [1, 2]


def test_reordering_lessons_produces_contiguous_positions():
    login_admin()
    course = create_course("lesson-reorder")
    l1 = create_lesson(course["id"], "1")
    l2 = create_lesson(course["id"], "2")
    l3 = create_lesson(course["id"], "3")

    # l1, l2, l3 -> move l3 up -> l1, l3, l2 -> move l3 up again -> l3, l1, l2
    assert client.post(f"/api/v1/admin/lessons/{l3['id']}/move", json={"direction": "up"}).status_code == 204
    assert client.post(f"/api/v1/admin/lessons/{l3['id']}/move", json={"direction": "up"}).status_code == 204

    detail = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    positions = [(lesson["id"], lesson["position"]) for lesson in detail["lessons"]]
    assert [position for _, position in positions] == [1, 2, 3]
    assert [lesson_id for lesson_id, _ in positions] == [l3["id"], l1["id"], l2["id"]]


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
    login_admin()
    course = create_course("no-lessons")

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("at least one lesson" in error for error in errors)


def test_publish_with_a_lesson_missing_a_video_names_that_lesson():
    login_admin()
    course = create_course("missing-video")
    lesson = create_lesson(course["id"], "missing-video", description="A lesson without a video.")
    add_complete_questions(lesson["id"], count=1)

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(lesson["title"] in error and "video" in error for error in errors)


def test_publish_with_a_lesson_missing_questions_names_that_lesson(monkeypatch):
    login_admin()
    course = create_course("missing-questions")
    lesson = create_lesson(course["id"], "missing-questions", description="A lesson without questions.")
    upload_video(lesson["slug"], monkeypatch)

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(lesson["title"] in error and "question" in error for error in errors)


def test_publish_with_missing_correct_choice_returns_422(monkeypatch):
    login_admin()
    course = create_course("no-correct-choice")
    lesson = create_lesson(course["id"], "no-correct-choice", description="d")
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
    assert any("at least one lesson" in error for error in errors)

    detail = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    assert detail["is_published"] is False


def test_dry_run_publish_reports_no_errors_for_complete_course(monkeypatch):
    login_admin()
    course = create_course("dry-run-complete", description="A complete test course.")
    lesson = create_lesson(course["id"], "dry-run-complete", description="A complete test lesson.")
    add_complete_questions(lesson["id"], count=1)
    upload_video(lesson["slug"], monkeypatch)
    add_objective(course["id"])

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish?dry_run=true")
    assert response.status_code == 200
    assert response.json()["errors"] == []

    detail = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    assert detail["is_published"] is False


def test_publish_complete_course_succeeds_and_appears_in_public_list(monkeypatch):
    login_admin()
    course = create_course("complete", description="A complete test course.")
    lesson = create_lesson(course["id"], "complete", description="A complete test lesson.")
    add_complete_questions(lesson["id"], count=1)
    upload_video(lesson["slug"], monkeypatch)
    add_objective(course["id"])

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 200
    assert response.json()["is_published"] is True

    public = client.get("/api/v1/courses")
    assert course["slug"] in [item["slug"] for item in public.json()]


def test_publishing_a_course_publishes_its_lessons_so_the_quiz_is_servable(monkeypatch):
    login_admin()
    course = create_course("publish-cascades", description="A complete test course.")
    lesson = create_lesson(course["id"], "publish-cascades", description="d")
    add_complete_questions(lesson["id"], count=1)
    upload_video(lesson["slug"], monkeypatch)
    add_objective(course["id"])

    assert lesson["is_published"] is False

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 200
    assert response.json()["lessons"][0]["is_published"] is True

    detail = client.get(f"/api/v1/courses/{course['slug']}").json()
    assert len(detail["lessons"]) == 1

    quiz = client.get(f"/api/v1/courses/{course['slug']}/quiz")
    assert quiz.status_code == 200
    assert quiz.json()["question_count"] == 1


def test_unpublish_removes_from_public_list(monkeypatch):
    login_admin()
    course = create_course("unpublish", description="A course to unpublish.")
    lesson = create_lesson(course["id"], "unpublish", description="d")
    add_complete_questions(lesson["id"], count=1)
    upload_video(lesson["slug"], monkeypatch)
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


# --- learning objectives, program metadata (feature 020) --------------------


def _make_publishable_course(slug_suffix, monkeypatch, **course_overrides):
    course = create_course(slug_suffix, description="A complete test course.")
    if course_overrides:
        response = client.patch(f"/api/v1/admin/courses/{course['id']}", json=course_overrides)
        assert response.status_code == 200, response.text
        course = response.json()
    lesson = create_lesson(course["id"], slug_suffix, description="A complete test lesson.")
    add_complete_questions(lesson["id"], count=1)
    upload_video(lesson["slug"], monkeypatch)
    add_objective(course["id"])
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
    lesson = create_lesson(course["id"], "no-objectives", description="d")
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
    assert "Accounting" in body["technical"]
    assert "Behavioral Ethics" in body["non_technical"]


def test_meta_program_levels_lists_all_five():
    response = client.get("/api/v1/meta/program-levels")
    assert response.status_code == 200
    assert response.json()["levels"] == ["basic", "intermediate", "advanced", "update", "overview"]
