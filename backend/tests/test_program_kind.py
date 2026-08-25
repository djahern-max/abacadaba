"""Feature 029: general programs. A course offered as ordinary education
rather than as a CPE program shows no CPE furniture and clears a relaxed
publish gate - see current-feature.md. Named test_program_kind.py rather
than folded into test_admin_content.py/test_certificates.py/test_courses.py
because it is one coherent feature with its own fixtures, not a handful of
one-off cases bolted onto those files."""

import io
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from app.constants.program_kind import PROGRAM_KIND_CPE
from app.db import SessionLocal
from app.main import app
from app.models.attempt import Attempt
from app.models.attempt_answer import AttemptAnswer
from app.models.choice import Choice
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.question import Question
from app.models.session import Session as SessionModel
from app.models.subject_matter_expert import SubjectMatterExpert
from app.models.user import User
from app.services import admin_content
from app.services import courses as courses_service
from app.services import storage

client = TestClient(app)

SLUG_PREFIX = "test-program-kind"
ADMIN_EMAIL = "program-kind-admin@example.com"
MEMBER_EMAIL = "program-kind-member@example.com"
PASSWORD = "correct-horse-battery"

FORBIDDEN_WORDS = ["cpe", "nasba", "credit", "field of study", "sponsor"]


def assert_no_forbidden_words(payload_text: str) -> None:
    lowered = payload_text.lower()
    for word in FORBIDDEN_WORDS:
        assert word not in lowered, f'forbidden word "{word}" found in: {payload_text}'


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
    db.execute(delete(SubjectMatterExpert).where(SubjectMatterExpert.name.like(f"{SLUG_PREFIX}%")))
    db.execute(delete(SessionModel).where(SessionModel.user_id.in_(user_ids)))
    db.execute(delete(User).where(User.email.in_(emails)))
    db.commit()
    db.close()


# --- helpers, modelled on tests/test_admin_content.py's ----------------------


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
    # program_kind is not settable at creation (AdminCourseCreate has no
    # such field - creation always starts 'cpe', matching the model's
    # server default) - so it's applied here as a follow-up PATCH, which is
    # always allowed on an unpublished course.
    program_kind = overrides.pop("program_kind", None)
    payload = {"title": f"Program Kind Test Course {slug_suffix}", "slug": f"{SLUG_PREFIX}-{slug_suffix}"}
    payload.update(overrides)
    response = client.post("/api/v1/admin/courses", json=payload)
    assert response.status_code == 201, response.text
    course = response.json()
    if program_kind is not None:
        patch = client.patch(f"/api/v1/admin/courses/{course['id']}", json={"program_kind": program_kind})
        assert patch.status_code == 200, patch.text
        course = patch.json()
    return course


def add_objective(course_id, text="Explain the objective."):
    response = client.post(f"/api/v1/admin/courses/{course_id}/objectives", json={"text": text})
    assert response.status_code == 201, response.text
    return response.json()


def add_question(lesson_id, prompt="Question?", kind="assessment", choice_count=4, objective_id=None, feedback=None):
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
        update_response = client.patch(f"/api/v1/admin/questions/{question_id}", json=updates)
        assert update_response.status_code == 200, update_response.text
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
            "review_cycle": "biennial",
        },
    )
    assert response.status_code == 200, response.text
    return developer, reviewer


def set_expiration(course_id, expires_on="2030-01-01"):
    response = client.patch(f"/api/v1/admin/courses/{course_id}", json={"expires_on": expires_on})
    assert response.status_code == 200, response.text


def make_publishable_cpe_course(slug_suffix, monkeypatch, **course_overrides):
    """A minimal course that clears the full CPE gate - the baseline every
    relaxed-rule test breaks in exactly one way."""
    course = create_course(slug_suffix, description="A complete test course.")
    if course_overrides:
        response = client.patch(f"/api/v1/admin/courses/{course['id']}", json=course_overrides)
        assert response.status_code == 200, response.text
        course = response.json()
    lesson = course["lessons"][0]
    objective = add_objective(course["id"])
    add_question(lesson["id"], "Q1", objective_id=objective["id"])
    add_question(lesson["id"], "Q2", objective_id=objective["id"])
    upload_video(lesson["slug"], monkeypatch)
    response = client.patch(
        f"/api/v1/admin/lessons/{lesson['id']}", json={"duration_seconds": 600, "required_watch_ratio": 0}
    )
    assert response.status_code == 200, response.text
    add_review_chain(course["id"], slug_suffix)
    set_expiration(course["id"])
    response = client.post(f"/api/v1/admin/courses/{course['id']}/credit")
    assert response.status_code == 200, response.text
    course = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    return course, lesson


def make_minimal_general_course(slug_suffix, monkeypatch, **course_overrides):
    """The smallest course a general publish is meant to accept: one
    objective, one assessment question, a video of any length, no reviewer,
    no computed credit - acceptance criterion 1."""
    course = create_course(slug_suffix, description="A minimal general course.", program_kind="general")
    if course_overrides:
        response = client.patch(f"/api/v1/admin/courses/{course['id']}", json=course_overrides)
        assert response.status_code == 200, response.text
        course = response.json()
    lesson = course["lessons"][0]
    objective = add_objective(course["id"])
    add_question(lesson["id"], "Only question?", objective_id=objective["id"])
    upload_video(lesson["slug"], monkeypatch)
    client.patch(f"/api/v1/admin/lessons/{lesson['id']}", json={"required_watch_ratio": 0})
    set_expiration(course["id"])
    course = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    return course, lesson


def publish(course_id):
    return client.post(f"/api/v1/admin/courses/{course_id}/publish")


# --- Part 1: the column -------------------------------------------------------


def test_new_course_defaults_to_cpe():
    login_admin()
    course = create_course("defaults")
    assert course["program_kind"] == "cpe"


def test_program_kind_rejects_unknown_value():
    login_admin()
    course = create_course("bad-value")

    db = SessionLocal()
    with pytest.raises(IntegrityError):
        db.execute(update(Course).where(Course.id == course["id"]).values(program_kind="nonsense"))
        db.flush()
    db.rollback()
    db.close()


# --- acceptance criterion 1: a minimal general course publishes -------------


def test_minimal_general_course_publishes(monkeypatch):
    login_admin()
    course, _ = make_minimal_general_course("minimal-publish", monkeypatch)
    response = publish(course["id"])
    assert response.status_code == 200, response.text


# --- Part 2/guard test: the public payload omits CPE fields entirely --------


def test_general_course_public_payload_has_no_cpe_words(monkeypatch):
    login_admin()
    course, _ = make_minimal_general_course("guard-payload", monkeypatch)
    publish(course["id"])
    client.cookies.clear()

    response = client.get(f"/api/v1/courses/{course['slug']}")
    assert response.status_code == 200
    body = response.json()

    assert "field_of_study" not in body
    assert "credit_award" not in body
    assert "sponsor_registry_status" not in body
    assert "expires_on" not in body
    assert "delivery_method" not in body
    assert_no_forbidden_words(response.text)


def test_cpe_course_public_payload_is_unchanged(monkeypatch):
    login_admin()
    course, _ = make_publishable_cpe_course("guard-cpe-unchanged", monkeypatch)
    publish(course["id"])
    client.cookies.clear()

    response = client.get(f"/api/v1/courses/{course['slug']}")
    assert response.status_code == 200
    body = response.json()
    assert body["program_kind"] == "cpe"
    assert body["field_of_study"] == course["field_of_study"]
    assert body["credit_award"] is not None
    assert "sponsor_registry_status" in body
    assert "expires_on" in body


# --- Part 3: the not-registered notice is derived on both fields -----------


def test_general_course_shows_no_not_registered_notice_even_when_unregistered(monkeypatch):
    login_admin()
    client.patch("/api/v1/admin/sponsor", json={"registry_status": "not_registered"})
    course, _ = make_minimal_general_course("no-notice", monkeypatch)
    publish(course["id"])
    client.cookies.clear()

    body = client.get(f"/api/v1/courses/{course['slug']}").json()
    assert "sponsor_registry_status" not in body
    client.patch("/api/v1/admin/sponsor", json={"registry_status": "registered"})


# --- Part 3: program_kind may not change while published --------------------


def test_program_kind_change_refused_while_published(monkeypatch):
    login_admin()
    course, _ = make_minimal_general_course("locked-general", monkeypatch)
    publish(course["id"])

    response = client.patch(f"/api/v1/admin/courses/{course['id']}", json={"program_kind": "cpe"})
    assert response.status_code == 409


def test_program_kind_change_allowed_after_unpublishing(monkeypatch):
    login_admin()
    course, _ = make_minimal_general_course("unpublish-then-switch", monkeypatch)
    publish(course["id"])

    client.post(f"/api/v1/admin/courses/{course['id']}/unpublish")
    response = client.patch(f"/api/v1/admin/courses/{course['id']}", json={"program_kind": "cpe"})
    assert response.status_code == 200, response.text
    assert response.json()["program_kind"] == "cpe"


def test_general_course_switched_to_cpe_must_clear_the_full_cpe_gate(monkeypatch):
    login_admin()
    course, _ = make_minimal_general_course("switch-needs-full-gate", monkeypatch)
    client.patch(f"/api/v1/admin/courses/{course['id']}", json={"program_kind": "cpe"})

    # Still missing a developer/reviewer/computed credit - the CPE gate, not
    # the general one, must now apply.
    response = publish(course["id"])
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("developer" in error for error in errors)


# --- Part 5: each relaxed rule, general passes / CPE still refused ---------


def test_field_of_study_relaxed_for_general_but_not_cpe(monkeypatch):
    # field_of_study is CHECK-constrained to a fixed list of real values
    # (ck_courses_field_of_study) and can never actually be blank in the
    # database, through this API or any other - so both sides of this
    # relaxation are exercised at the service layer directly, on an
    # unpersisted mutation, rather than via a PATCH the database would
    # refuse regardless of program_kind.
    login_admin()
    general, _ = make_minimal_general_course("relax-fos-general", monkeypatch)
    cpe, _ = make_publishable_cpe_course("relax-fos-cpe", monkeypatch)

    db = SessionLocal()
    general_course = admin_content.get_course(db, general["id"])
    general_course.field_of_study = ""
    general_errors = admin_content.validate_for_publish(db, general_course)
    assert not any("Field of study is required" in error for error in general_errors)

    cpe_course = admin_content.get_course(db, cpe["id"])
    cpe_course.field_of_study = ""
    cpe_errors = admin_content.validate_for_publish(db, cpe_course)
    assert any("Field of study is required" in error for error in cpe_errors)
    db.rollback()
    db.close()


def test_review_chain_relaxed_for_general_but_not_cpe(monkeypatch):
    login_admin()
    general, _ = make_minimal_general_course("relax-review-general", monkeypatch)
    assert general["developer_id"] is None
    assert general["reviewer_id"] is None
    response = publish(general["id"])
    assert response.status_code == 200, response.text

    # A fresh CPE course that never gets a review chain - add_review_chain
    # PATCHes developer_id/reviewer_id/reviewed_at all at once, so there is
    # no way to "undo" it partially; build the missing-chain case directly.
    cpe = create_course("relax-review-cpe", description="Missing review chain.")
    lesson = cpe["lessons"][0]
    objective = add_objective(cpe["id"])
    add_question(lesson["id"], "Q1", objective_id=objective["id"])
    add_question(lesson["id"], "Q2", objective_id=objective["id"])
    upload_video(lesson["slug"], monkeypatch)
    client.patch(f"/api/v1/admin/lessons/{lesson['id']}", json={"duration_seconds": 600})
    set_expiration(cpe["id"])
    client.post(f"/api/v1/admin/courses/{cpe['id']}/credit")

    response = publish(cpe["id"])
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("developer" in error for error in errors)
    assert any("reviewer" in error for error in errors)
    assert any("review date" in error for error in errors)


def test_licensed_cpa_requirement_relaxed_for_general_but_not_cpe(monkeypatch):
    login_admin()
    general, general_lesson = make_minimal_general_course("relax-cpa-general", monkeypatch, field_of_study="Accounting")
    response = publish(general["id"])
    assert response.status_code == 200, response.text

    cpe, _ = make_publishable_cpe_course(
        "relax-cpa-cpe",
        monkeypatch,
        field_of_study="Accounting",
    )
    # Rebuild the review chain with no licensed CPA on either side.
    dev = create_sme("relax-cpa-cpe-dev2", is_licensed_cpa=False)
    rev = create_sme("relax-cpa-cpe-rev2", is_licensed_cpa=False)
    client.patch(
        f"/api/v1/admin/courses/{cpe['id']}",
        json={
            "developer_id": dev["id"],
            "reviewer_id": rev["id"],
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "review_cycle": "biennial",
        },
    )
    response = publish(cpe["id"])
    assert response.status_code == 422
    assert any("licensed CPA" in error for error in response.json()["detail"])


def test_credit_computed_requirement_relaxed_for_general_but_not_cpe(monkeypatch):
    login_admin()
    general, _ = make_minimal_general_course("relax-credit-general", monkeypatch)
    assert general["credit_computed_at"] is None
    response = publish(general["id"])
    assert response.status_code == 200, response.text

    cpe = create_course("relax-credit-cpe", description="Never had credit computed.")
    lesson = cpe["lessons"][0]
    objective = add_objective(cpe["id"])
    add_question(lesson["id"], "Q1", objective_id=objective["id"])
    add_question(lesson["id"], "Q2", objective_id=objective["id"])
    upload_video(lesson["slug"], monkeypatch)
    client.patch(f"/api/v1/admin/lessons/{lesson['id']}", json={"duration_seconds": 600})
    add_review_chain(cpe["id"], "relax-credit-cpe")
    set_expiration(cpe["id"])
    # Deliberately no POST .../credit call.

    response = publish(cpe["id"])
    assert response.status_code == 422
    assert any("Credit has not been computed" in error for error in response.json()["detail"])


def test_lesson_duration_requirement_relaxed_for_general_but_not_cpe(monkeypatch):
    login_admin()
    general, general_lesson = make_minimal_general_course("relax-duration-general", monkeypatch)
    assert general_lesson["duration_seconds"] is None
    response = publish(general["id"])
    assert response.status_code == 200, response.text

    cpe = create_course("relax-duration-cpe", description="Lesson with no duration.")
    lesson = cpe["lessons"][0]
    objective = add_objective(cpe["id"])
    add_question(lesson["id"], "Q1", objective_id=objective["id"])
    add_question(lesson["id"], "Q2", objective_id=objective["id"])
    upload_video(lesson["slug"], monkeypatch)
    # Deliberately no duration_seconds PATCH - av_is_additional_learning
    # defaults to True, so this lesson counts its runtime toward credit but
    # has none recorded.
    add_review_chain(cpe["id"], "relax-duration-cpe")
    set_expiration(cpe["id"])

    response = publish(cpe["id"])
    assert response.status_code == 422
    assert any("no duration" in error for error in response.json()["detail"])


def test_forced_choice_ban_relaxed_for_general_but_not_cpe(monkeypatch):
    login_admin()
    course = create_course("relax-fc-general", description="d", program_kind="general")
    lesson = course["lessons"][0]
    objective = add_objective(course["id"])
    add_question(lesson["id"], "True or false?", objective_id=objective["id"], choice_count=2)
    upload_video(lesson["slug"], monkeypatch)
    set_expiration(course["id"])
    response = publish(course["id"])
    assert response.status_code == 200, response.text

    cpe, cpe_lesson = make_publishable_cpe_course("relax-fc-cpe", monkeypatch)
    add_question(cpe_lesson["id"], "True or false too?", choice_count=2)
    response = publish(cpe["id"])
    assert response.status_code == 422
    assert any("forced-choice" in error for error in response.json()["detail"])


def test_review_feedback_requirement_relaxed_for_general_but_not_cpe(monkeypatch):
    login_admin()
    course = create_course("relax-feedback-general", description="d", program_kind="general")
    lesson = course["lessons"][0]
    objective = add_objective(course["id"])
    add_question(lesson["id"], "Assessment Q", objective_id=objective["id"])
    add_question(lesson["id"], "Review Q", kind="review")  # no feedback
    upload_video(lesson["slug"], monkeypatch)
    set_expiration(course["id"])
    response = publish(course["id"])
    assert response.status_code == 200, response.text

    cpe, cpe_lesson = make_publishable_cpe_course("relax-feedback-cpe", monkeypatch)
    add_question(cpe_lesson["id"], "Review Q no feedback", kind="review")
    response = publish(cpe["id"])
    assert response.status_code == 422
    assert any("needs feedback" in error for error in response.json()["detail"])


def test_objective_coverage_relaxed_for_general_but_not_cpe(monkeypatch):
    login_admin()
    course = create_course("relax-coverage-general", description="d", program_kind="general")
    lesson = course["lessons"][0]
    add_objective(course["id"], "Objective A")
    add_objective(course["id"], "Objective B")
    add_question(lesson["id"], "Only tags A", objective_id=None)
    upload_video(lesson["slug"], monkeypatch)
    set_expiration(course["id"])
    response = publish(course["id"])
    assert response.status_code == 200, response.text

    cpe, cpe_lesson = make_publishable_cpe_course("relax-coverage-cpe", monkeypatch)
    add_objective(cpe["id"], "Untagged objective")
    response = publish(cpe["id"])
    assert response.status_code == 422
    assert any("75%" in error for error in response.json()["detail"])


def test_credit_derived_question_minimums_relaxed_for_general_but_not_cpe(monkeypatch):
    login_admin()
    general, general_lesson = make_minimal_general_course("relax-minimums-general", monkeypatch)
    response = publish(general["id"])
    assert response.status_code == 200, response.text

    # A course computed to more than 0.2 credit needs more than 2 assessment
    # questions (6.01.2's chart) - only 2 are seeded, so this should refuse.
    cpe, cpe_lesson = make_publishable_cpe_course("relax-minimums-cpe", monkeypatch)
    client.patch(f"/api/v1/admin/lessons/{cpe_lesson['id']}", json={"duration_seconds": 1500})
    client.post(f"/api/v1/admin/courses/{cpe['id']}/credit")
    response = publish(cpe["id"])
    assert response.status_code == 422
    assert any("qualified assessment question(s)" in error for error in response.json()["detail"])


def test_credit_award_floor_relaxed_for_general_but_not_cpe(monkeypatch):
    login_admin()
    course = create_course("relax-floor-general", description="d", program_kind="general")
    lesson = course["lessons"][0]
    objective = add_objective(course["id"])
    add_question(lesson["id"], "Only question", objective_id=objective["id"])
    upload_video(lesson["slug"], monkeypatch)
    client.patch(f"/api/v1/admin/lessons/{lesson['id']}", json={"duration_seconds": 5})
    set_expiration(course["id"])
    # The Credit panel stays computable for a general course - frontend
    # task 3 - so exercise the relaxation for real: compute credit, confirm
    # it lands below the 0.2 floor, and confirm that still doesn't block.
    credit = client.post(f"/api/v1/admin/courses/{course['id']}/credit")
    assert credit.status_code == 200, credit.text
    assert Decimal(str(credit.json()["award"])) < Decimal("0.2")
    response = publish(course["id"])
    assert response.status_code == 200, response.text

    cpe, cpe_lesson = make_publishable_cpe_course("relax-floor-cpe", monkeypatch)
    client.patch(f"/api/v1/admin/lessons/{cpe_lesson['id']}", json={"duration_seconds": 5})
    client.post(f"/api/v1/admin/courses/{cpe['id']}/credit")
    response = publish(cpe["id"])
    assert response.status_code == 422
    assert any("below the" in error and "minimum" in error for error in response.json()["detail"])


def test_sponsor_profile_completeness_relaxed_to_name_only_for_general(monkeypatch):
    login_admin()
    client.patch("/api/v1/admin/sponsor", json={"registry_status": "registered", "national_registry_id": ""})
    course, _ = make_minimal_general_course("relax-sponsor-general", monkeypatch)
    response = publish(course["id"])
    assert response.status_code == 200, response.text

    client.patch("/api/v1/admin/sponsor", json={"name": ""})
    response = client.post(f"/api/v1/admin/courses/{course['id']}/unpublish")
    response = publish(course["id"])
    assert response.status_code == 422
    assert any("sponsor name" in error for error in response.json()["detail"])
    client.patch("/api/v1/admin/sponsor", json={"name": "Test Sponsor, Inc.", "national_registry_id": "123456"})


# --- Part 5: still enforced for a general course -----------------------------


def test_general_course_still_needs_at_least_one_objective(monkeypatch):
    login_admin()
    course = create_course("still-objective", description="d", program_kind="general")
    lesson = course["lessons"][0]
    add_question(lesson["id"], "Q")
    upload_video(lesson["slug"], monkeypatch)
    set_expiration(course["id"])
    response = publish(course["id"])
    assert response.status_code == 422
    assert any("learning objective" in error for error in response.json()["detail"])


def test_general_course_still_needs_at_least_one_assessment_question(monkeypatch):
    login_admin()
    course = create_course("still-assessment", description="d", program_kind="general")
    lesson = course["lessons"][0]
    add_objective(course["id"])
    upload_video(lesson["slug"], monkeypatch)
    set_expiration(course["id"])
    response = publish(course["id"])
    assert response.status_code == 422
    assert any("qualified assessment question" in error for error in response.json()["detail"])


def test_general_course_still_needs_the_four_real_policies(monkeypatch):
    from app.constants.policies import PLACEHOLDER_BODY
    from app.models.policy import Policy

    login_admin()
    course, _ = make_minimal_general_course("still-policies", monkeypatch)
    db = SessionLocal()
    db.execute(update(Policy).where(Policy.slug == "refund-and-cancellation").values(body=PLACEHOLDER_BODY))
    db.commit()
    db.close()

    response = publish(course["id"])
    assert response.status_code == 422
    assert any("Refund and Cancellation Policy" in error for error in response.json()["detail"])

    db = SessionLocal()
    db.execute(
        update(Policy).where(Policy.slug == "refund-and-cancellation").values(body="Real policy text for tests.")
    )
    db.commit()
    db.close()


def test_general_course_still_needs_pass_ratio_at_least_70_percent(monkeypatch):
    login_admin()
    course, _ = make_minimal_general_course("still-pass-ratio", monkeypatch)
    # pass_ratio floors at 0.70 via a CHECK constraint - assert that a
    # general course inherits the same floor rather than one relaxed to
    # zero, by confirming the PATCH itself is refused below it.
    response = client.patch(f"/api/v1/admin/courses/{course['id']}", json={"pass_ratio": 0.5})
    assert response.status_code == 422


# --- certificate and verify: guard test + CPE unchanged + snapshotting -----


def get_questions_for_slug(slug):
    db = SessionLocal()
    stmt = select(Question).join(Lesson).join(Course).where(Course.slug == slug).order_by(Question.position)
    questions = db.execute(stmt).scalars().all()
    result = []
    for question in questions:
        correct_choice = next(c for c in question.choices if c.is_correct)
        result.append({"question_id": question.id, "correct_choice_id": correct_choice.id})
    db.close()
    return result


def answer(attempt_id, question_id, choice_id):
    return client.post(
        f"/api/v1/attempts/{attempt_id}/answers",
        json={"question_id": question_id, "choice_id": choice_id},
    )


def start_and_pass(slug):
    register_and_login(MEMBER_EMAIL)
    response = client.post(f"/api/v1/courses/{slug}/attempts")
    assert response.status_code == 201, response.text
    attempt_id = response.json()["attempt_id"]
    for q in get_questions_for_slug(slug):
        answer(attempt_id, q["question_id"], q["correct_choice_id"])
    return attempt_id


def extract_pdf_text(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() for page in reader.pages)


def test_general_certificate_pdf_and_verify_payload_have_no_cpe_words(monkeypatch):
    login_admin()
    # conftest.py's shared DEFAULT_SPONSOR name ("Test Sponsor, Inc.")
    # coincidentally contains the substring "sponsor" as part of its own
    # chosen organization name, printed on the general certificate as
    # "Issued by" - legitimate output, not a leak of CPE vocabulary. Use an
    # org name without that coincidence so this guard test isolates what it
    # actually means to check: that nothing this feature generates leaks
    # the words, not that no organization may ever choose one containing
    # them.
    client.patch("/api/v1/admin/sponsor", json={"name": "Example Learning Co."})
    course, _ = make_minimal_general_course("cert-guard", monkeypatch)
    response = publish(course["id"])
    assert response.status_code == 200, response.text
    client.cookies.clear()

    attempt_id = start_and_pass(course["slug"])
    claim = client.post(f"/api/v1/attempts/{attempt_id}/certificate", json={})
    assert claim.status_code == 200, claim.text
    code = claim.json()["certificate_code"]
    assert_no_forbidden_words(claim.text)

    pdf_response = client.get(f"/api/v1/attempts/{attempt_id}/certificate.pdf")
    assert pdf_response.status_code == 200
    pdf_text = extract_pdf_text(pdf_response.content)
    assert_no_forbidden_words(pdf_text)

    verify = client.get(f"/api/v1/certificates/{code}")
    assert verify.status_code == 200
    assert_no_forbidden_words(verify.text)
    assert verify.json()["program_kind"] == "general"
    assert verify.json()["issued_by"]


def test_cpe_certificate_is_unaffected(monkeypatch):
    login_admin()
    client.patch("/api/v1/admin/sponsor", json={"registry_status": "registered", "national_registry_id": "123456"})
    course, _ = make_publishable_cpe_course("cert-cpe-unaffected", monkeypatch, field_of_study="Taxes")
    # Taxes needs a CPA/attorney/EA - add_review_chain's default developer is
    # a licensed CPA already, so this publishes unchanged.
    response = publish(course["id"])
    assert response.status_code == 200, response.text
    client.cookies.clear()

    attempt_id = start_and_pass(course["slug"])
    claim = client.post(f"/api/v1/attempts/{attempt_id}/certificate", json={})
    assert claim.status_code == 200, claim.text
    body = claim.json()
    assert body["program_kind"] == "cpe"
    assert body["field_of_study"] == "Taxes"
    assert body["sponsor_name"]

    pdf_response = client.get(f"/api/v1/attempts/{attempt_id}/certificate.pdf")
    text = extract_pdf_text(pdf_response.content)
    assert "Taxes" in text
    assert "50-minute" in text


def test_certificate_claimed_as_general_stays_general_after_course_switches_to_cpe(monkeypatch):
    login_admin()
    course, _ = make_minimal_general_course("snapshot-holds", monkeypatch)
    response = publish(course["id"])
    assert response.status_code == 200, response.text
    client.cookies.clear()

    attempt_id = start_and_pass(course["slug"])
    claim = client.post(f"/api/v1/attempts/{attempt_id}/certificate", json={})
    code = claim.json()["certificate_code"]
    assert claim.json()["program_kind"] == "general"

    register_and_login(ADMIN_EMAIL, is_admin=True)
    client.post(f"/api/v1/admin/courses/{course['id']}/unpublish")
    client.patch(f"/api/v1/admin/courses/{course['id']}", json={"program_kind": "cpe"})

    verify = client.get(f"/api/v1/certificates/{code}")
    assert verify.json()["program_kind"] == "general"
    assert verify.json()["issued_by"]


def test_null_cert_program_kind_falls_back_to_cpe(monkeypatch):
    login_admin()
    client.patch("/api/v1/admin/sponsor", json={"registry_status": "registered", "national_registry_id": "123456"})
    course, _ = make_publishable_cpe_course("null-fallback", monkeypatch)
    response = publish(course["id"])
    assert response.status_code == 200, response.text
    client.cookies.clear()

    attempt_id = start_and_pass(course["slug"])
    client.post(f"/api/v1/attempts/{attempt_id}/certificate", json={})

    db = SessionLocal()
    db.execute(
        update(Attempt).where(Attempt.public_id == uuid.UUID(attempt_id)).values(cert_program_kind=None)
    )
    db.commit()
    db.close()

    pdf_response = client.get(f"/api/v1/attempts/{attempt_id}/certificate.pdf")
    assert pdf_response.status_code == 200
    text = extract_pdf_text(pdf_response.content)
    assert "50-minute" in text  # renders the CPE fields, not the general omissions


# --- Part 6: the footer EXISTS query -----------------------------------------


def test_footer_true_with_one_published_cpe_course(monkeypatch):
    login_admin()
    course, _ = make_publishable_cpe_course("footer-true", monkeypatch)
    publish(course["id"])
    client.cookies.clear()

    response = client.get("/api/v1/meta/site-status")
    assert response.status_code == 200
    assert response.json()["show_policy_footer"] is True


@pytest.fixture
def no_other_published_cpe_courses():
    """Temporarily unpublishes any other published CPE course so the two
    tests below can assert show_policy_footer's False case in isolation,
    without permanently touching real data outside this test file's own
    fixtures - restored unconditionally afterward."""
    db = SessionLocal()
    other_ids = list(
        db.execute(
            select(Course.id).where(
                Course.is_published.is_(True),
                Course.program_kind == PROGRAM_KIND_CPE,
                Course.slug.notlike(f"{SLUG_PREFIX}%"),
            )
        ).scalars()
    )
    if other_ids:
        db.execute(update(Course).where(Course.id.in_(other_ids)).values(is_published=False))
        db.commit()
    db.close()

    yield

    if other_ids:
        db = SessionLocal()
        db.execute(update(Course).where(Course.id.in_(other_ids)).values(is_published=True))
        db.commit()
        db.close()


def test_footer_false_with_only_published_general_courses(monkeypatch, no_other_published_cpe_courses):
    login_admin()
    course, _ = make_minimal_general_course("footer-false", monkeypatch)
    publish(course["id"])

    db = SessionLocal()
    assert courses_service.show_policy_footer(db) is False
    db.close()


def test_footer_false_with_an_unpublished_cpe_course(monkeypatch, no_other_published_cpe_courses):
    login_admin()
    make_publishable_cpe_course("footer-unpublished", monkeypatch)
    # Deliberately not published.

    db = SessionLocal()
    assert courses_service.show_policy_footer(db) is False
    db.close()
