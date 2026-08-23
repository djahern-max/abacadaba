import io
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

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
from app.services import credit, storage

client = TestClient(app)

SLUG_PREFIX = "test-credit"
ADMIN_EMAIL = "admin-credit@example.com"
PASSWORD = "correct-horse-battery"


@pytest.fixture(autouse=True)
def cleanup():
    client.cookies.clear()

    yield

    client.cookies.clear()
    db = SessionLocal()
    user_ids = select(User.id).where(User.email == ADMIN_EMAIL)
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
    db.execute(delete(User).where(User.email == ADMIN_EMAIL))
    db.commit()
    db.close()


def login_admin():
    client.post(
        "/api/v1/auth/register",
        json={"email": ADMIN_EMAIL, "password": PASSWORD, "display_name": "Test Admin"},
    )
    db = SessionLocal()
    user = db.execute(select(User).where(User.email == ADMIN_EMAIL)).scalar_one()
    user.is_admin = True
    db.commit()
    db.close()


def create_course(slug_suffix, **overrides):
    payload = {"title": f"Credit Test Course {slug_suffix}", "slug": f"{SLUG_PREFIX}-{slug_suffix}"}
    payload.update(overrides)
    response = client.post("/api/v1/admin/courses", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def upload_video(slug, monkeypatch):
    monkeypatch.setattr(storage, "upload_fileobj", lambda fileobj, key, content_type: None)
    response = client.post(
        f"/api/v1/admin/lessons/{slug}/video",
        files={"file": ("video.mp4", io.BytesIO(b"data"), "video/mp4")},
    )
    assert response.status_code == 200, response.text


def add_questions(lesson_id, count, kind="assessment"):
    # Prompt includes kind so two calls (e.g. review then assessment) never
    # produce an exact-duplicate prompt across kinds - feature 023's publish
    # check refuses that (6.01.2).
    for i in range(count):
        question = client.post(
            f"/api/v1/admin/lessons/{lesson_id}/questions", json={"prompt": f"{kind} question {i}"}
        )
        assert question.status_code == 201, question.text
        question_id = question.json()["id"]
        if kind != "assessment":
            update = client.patch(f"/api/v1/admin/questions/{question_id}", json={"kind": kind})
            assert update.status_code == 200, update.text
        # 4 choices, not 2: feature 023's MIN_CHOICES_ASSESSMENT (>= 3) and
        # the "a two-choice question doesn't count toward the review
        # minimum" rule both key off choice count.
        for j in range(4):
            choice = client.post(
                f"/api/v1/admin/questions/{question_id}/choices",
                json={"text": f"Choice {j}", "is_correct": j == 0},
            )
            assert choice.status_code == 201, choice.text


def add_objective(course_id):
    response = client.post(f"/api/v1/admin/courses/{course_id}/objectives", json={"text": "Explain the objective."})
    assert response.status_code == 201, response.text


def add_review_chain(course_id, slug_suffix):
    developer = client.post(
        "/api/v1/admin/smes",
        json={"name": f"{SLUG_PREFIX} dev {slug_suffix}", "credentials": "CPA", "is_licensed_cpa": True},
    )
    assert developer.status_code == 201, developer.text
    reviewer = client.post(
        "/api/v1/admin/smes", json={"name": f"{SLUG_PREFIX} rev {slug_suffix}", "credentials": "CPA"}
    )
    assert reviewer.status_code == 201, reviewer.text
    response = client.patch(
        f"/api/v1/admin/courses/{course_id}",
        json={
            "developer_id": developer.json()["id"],
            "reviewer_id": reviewer.json()["id"],
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "review_notes": None,
            "review_cycle": "biennial",
        },
    )
    assert response.status_code == 200, response.text


def _publishable_course(monkeypatch, slug_suffix):
    """One 1500s A/V lesson, six questions, objective, and review chain -
    computes to 0.6 credit: (1500/60 + 6*1.85) / 50 = 0.722 -> floor(3.61)/5.
    Feature 023: at 0.6 credit, 5.01.2.1 requires 2 review questions and
    6.01.2 requires 4 assessment questions - the six questions below are
    typed 2 review / 4 assessment (add_questions' default kind) to match
    exactly, each with 4 choices so MIN_CHOICES_ASSESSMENT (>= 3) clears too."""
    login_admin()
    course = create_course(slug_suffix, description="A complete test course.")
    lesson = course["lessons"][0]
    upload_video(lesson["slug"], monkeypatch)
    response = client.patch(f"/api/v1/admin/lessons/{lesson['id']}", json={"duration_seconds": 1500})
    assert response.status_code == 200, response.text
    add_questions(lesson["id"], 2, kind="review")
    add_questions(lesson["id"], 4, kind="assessment")
    add_objective(course["id"])
    add_review_chain(course["id"], slug_suffix)
    response = client.post(f"/api/v1/admin/courses/{course['id']}/credit")
    assert response.status_code == 200, response.text
    return client.get(f"/api/v1/admin/courses/{course['id']}").json(), lesson


# --- round_down (7.01) ---------------------------------------------------------


def test_round_down_never_rounds_up():
    assert credit.round_down(Decimal("0.599")) == Decimal("0.4")


def test_round_down_below_one_fifth_is_zero():
    assert credit.round_down(Decimal("0.15")) == Decimal("0.0")


def test_round_down_exact_one_fifth_boundary_is_awarded():
    assert credit.round_down(Decimal("0.2")) == Decimal("0.2")


# --- compute (7.02.6, 7.02.7) --------------------------------------------------


def test_all_video_course_computes_expected_credit(monkeypatch):
    login_admin()
    course = create_course("all-video")
    lesson = course["lessons"][0]
    upload_video(lesson["slug"], monkeypatch)
    response = client.patch(f"/api/v1/admin/lessons/{lesson['id']}", json={"duration_seconds": 486})
    assert response.status_code == 200, response.text
    add_questions(lesson["id"], 8)

    response = client.post(f"/api/v1/admin/courses/{course['id']}/credit")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["word_count"] == 0
    assert body["av_seconds"] == 486
    assert body["question_count"] == 8
    assert Decimal(str(body["award"])) == Decimal("0.4")


def test_credit_is_unchanged_by_the_review_assessment_type_split(monkeypatch):
    # Same shape as test_all_video_course_computes_expected_credit (486s,
    # 8 questions, 0.4 credit) but split 3 review / 5 assessment - feature
    # 023 must not narrow credit's count to assessment-only questions.
    login_admin()
    course = create_course("type-split")
    lesson = course["lessons"][0]
    upload_video(lesson["slug"], monkeypatch)
    response = client.patch(f"/api/v1/admin/lessons/{lesson['id']}", json={"duration_seconds": 486})
    assert response.status_code == 200, response.text
    add_questions(lesson["id"], 3, kind="review")
    add_questions(lesson["id"], 5, kind="assessment")

    response = client.post(f"/api/v1/admin/courses/{course['id']}/credit")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["question_count"] == 8
    assert Decimal(str(body["award"])) == Decimal("0.4")


def test_narration_segment_contributes_words_not_its_runtime(monkeypatch):
    login_admin()
    course = create_course("narration")
    lesson1 = course["lessons"][0]
    upload_video(lesson1["slug"], monkeypatch)
    response = client.patch(f"/api/v1/admin/lessons/{lesson1['id']}", json={"duration_seconds": 300})
    assert response.status_code == 200, response.text
    add_questions(lesson1["id"], 1)

    lesson2_response = client.post(
        f"/api/v1/admin/courses/{course['id']}/lessons", json={"title": "Narration segment"}
    )
    assert lesson2_response.status_code == 201, lesson2_response.text
    lesson2 = lesson2_response.json()
    upload_video(lesson2["slug"], monkeypatch)
    # A large duration that must NOT enter the A/V term, since this segment
    # is flagged as narration of the text - only its word count should count.
    response = client.patch(
        f"/api/v1/admin/lessons/{lesson2['id']}",
        json={"duration_seconds": 999999, "av_is_additional_learning": False, "word_count": 1800},
    )
    assert response.status_code == 200, response.text

    response = client.post(f"/api/v1/admin/courses/{course['id']}/credit")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["word_count"] == 1800
    assert body["av_seconds"] == 300
    assert body["question_count"] == 1
    # (1800/180 + 300/60 + 1*1.85) / 50 = 16.85/50 = 0.337 -> floor(1.685)/5
    assert Decimal(str(body["award"])) == Decimal("0.2")


def test_raw_credit_below_min_awardable_is_zero_and_publish_names_the_gap(monkeypatch):
    login_admin()
    course = create_course("below-min")
    lesson = course["lessons"][0]
    upload_video(lesson["slug"], monkeypatch)
    response = client.patch(f"/api/v1/admin/lessons/{lesson['id']}", json={"duration_seconds": 10})
    assert response.status_code == 200, response.text
    add_questions(lesson["id"], 1)
    add_objective(course["id"])
    add_review_chain(course["id"], "below-min")

    response = client.post(f"/api/v1/admin/courses/{course['id']}/credit")
    assert response.status_code == 200, response.text
    assert Decimal(str(response.json()["award"])) == Decimal("0.0")

    publish = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert publish.status_code == 422
    errors = publish.json()["detail"]
    assert any("below the 0.2" in error and "more seconds" in error for error in errors)


def test_editing_a_question_makes_credit_read_stale_and_recompute_clears_it(monkeypatch):
    course, lesson = _publishable_course(monkeypatch, "stale")
    assert course["credit_computed_at"] is not None
    assert course["credit_computed_at"] >= course["content_updated_at"]

    question_id = client.get(f"/api/v1/admin/lessons/{lesson['id']}").json()["questions"][0]["id"]
    response = client.patch(f"/api/v1/admin/questions/{question_id}", json={"prompt": "Updated prompt?"})
    assert response.status_code == 200, response.text

    course = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    assert course["credit_computed_at"] < course["content_updated_at"]

    publish = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert publish.status_code == 422
    errors = publish.json()["detail"]
    assert any("changed since credit was last computed" in error for error in errors)

    recompute = client.post(f"/api/v1/admin/courses/{course['id']}/credit")
    assert recompute.status_code == 200, recompute.text

    course = client.get(f"/api/v1/admin/courses/{course['id']}").json()
    assert course["credit_computed_at"] >= course["content_updated_at"]

    # Recomputing cleared credit's own staleness; the review chain (a
    # separate concern from feature 021) is now stale from the same edit
    # and would need its own re-review before this course could publish -
    # out of scope for this test, which is only about credit's staleness.
    publish = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert publish.status_code == 422
    errors = publish.json()["detail"]
    assert not any("changed since credit was last computed" in error for error in errors)
    assert any("changed since it was reviewed" in error for error in errors)


def test_publish_refused_when_av_segment_has_no_duration(monkeypatch):
    login_admin()
    course = create_course("no-duration")
    lesson = course["lessons"][0]
    upload_video(lesson["slug"], monkeypatch)
    add_questions(lesson["id"], 1)
    add_objective(course["id"])
    add_review_chain(course["id"], "no-duration")

    response = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("counts its runtime toward credit but has no duration" in error for error in errors)


def test_public_course_payload_carries_the_credit(monkeypatch):
    course, _ = _publishable_course(monkeypatch, "public")
    publish = client.post(f"/api/v1/admin/courses/{course['id']}/publish")
    assert publish.status_code == 200, publish.text

    response = client.get(f"/api/v1/courses/{course['slug']}")
    assert response.status_code == 200
    assert Decimal(str(response.json()["credit_award"])) == Decimal("0.6")


def test_get_credit_before_any_computation_is_all_null():
    login_admin()
    course = create_course("never-computed")

    response = client.get(f"/api/v1/admin/courses/{course['id']}/credit")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["computed_at"] is None
    assert body["award"] is None
