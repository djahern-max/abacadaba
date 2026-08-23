import uuid
from decimal import Decimal
from io import BytesIO

import pytest
from pypdf import PdfReader
from fastapi.testclient import TestClient
from sqlalchemy import delete, select, update

from app.constants.delivery_methods import DELIVERY_METHOD_SELF_STUDY
from app.db import SessionLocal
from app.main import app
from app.models.attempt import Attempt
from app.models.choice import Choice
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.question import Question
from app.models.session import Session as SessionModel
from app.models.sponsor_profile import SponsorProfile
from app.models.user import User

client = TestClient(app)

COURSE_SLUG = "test-course-certificates"
SIGNED_IN_EMAIL = "certificates-user@example.com"
SIGNED_IN_PASSWORD = "correct-horse-battery"
SIGNED_IN_DISPLAY_NAME = "Grace Hopper Account"
GENERIC_EMAIL = "certificates-flow-user@example.com"
COURSE_FIELD_OF_STUDY = "Regulatory Ethics"
COURSE_CREDIT_AWARD = Decimal("1.2")
SPONSOR_NAME = "Certificates Test Sponsor"
SPONSOR_REGISTRY_ID = "555444"
SPONSOR_STATE_REGISTRY_IDS = "NH #777"


@pytest.fixture(autouse=True)
def seed_test_course():
    db = SessionLocal()

    course = Course(
        slug=COURSE_SLUG,
        title="Course For Certificates",
        description="Used to test the certificate endpoints.",
        is_published=True,
        field_of_study=COURSE_FIELD_OF_STUDY,
        credit_award=COURSE_CREDIT_AWARD,
    )
    db.add(course)
    db.flush()

    lesson = Lesson(
        course_id=course.id,
        position=1,
        slug=f"{COURSE_SLUG}-lesson",
        title="Lesson For Certificates",
        description="Used to test the certificate endpoints.",
        duration_seconds=300,
        is_published=True,
        required_watch_ratio=0,  # ungated: these tests cover certificates, not watch gating
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

    db.execute(
        update(SponsorProfile)
        .where(SponsorProfile.id == 1)
        .values(
            name=SPONSOR_NAME,
            national_registry_id=SPONSOR_REGISTRY_ID,
            state_registry_ids=SPONSOR_STATE_REGISTRY_IDS,
        )
    )
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
    emails = [SIGNED_IN_EMAIL, GENERIC_EMAIL]
    user_ids = select(User.id).where(User.email.in_(emails))
    db.execute(delete(SessionModel).where(SessionModel.user_id.in_(user_ids)))
    db.execute(delete(User).where(User.email.in_(emails)))
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


def answer(attempt_id, question_id, choice_id):
    return client.post(
        f"/api/v1/attempts/{attempt_id}/answers",
        json={"question_id": question_id, "choice_id": choice_id},
    )


def ensure_signed_in():
    if "session_id" in client.cookies:
        return
    client.post(
        "/api/v1/auth/register",
        json={
            "email": GENERIC_EMAIL,
            "password": SIGNED_IN_PASSWORD,
            "display_name": "Certificates Flow User",
        },
    )


def start_and_pass_attempt():
    ensure_signed_in()
    response = client.post(f"/api/v1/courses/{COURSE_SLUG}/attempts")
    attempt_id = response.json()["attempt_id"]
    for q in get_questions():
        answer(attempt_id, q["question_id"], q["correct_choice_id"])
    return attempt_id


def start_and_fail_attempt():
    ensure_signed_in()
    response = client.post(f"/api/v1/courses/{COURSE_SLUG}/attempts")
    attempt_id = response.json()["attempt_id"]
    questions = get_questions()
    for q in questions[:2]:
        answer(attempt_id, q["question_id"], q["correct_choice_id"])
    for q in questions[2:]:
        answer(attempt_id, q["question_id"], q["wrong_choice_id"])
    return attempt_id


def start_incomplete_attempt():
    ensure_signed_in()
    response = client.post(f"/api/v1/courses/{COURSE_SLUG}/attempts")
    attempt_id = response.json()["attempt_id"]
    questions = get_questions()
    answer(attempt_id, questions[0]["question_id"], questions[0]["correct_choice_id"])
    return attempt_id


def start_and_pass_legacy_anonymous_attempt():
    # Simulates an attempt created before this feature shipped, when
    # POST /attempts didn't require a signed in user. Built directly against
    # the DB rather than through the API, which no longer allows it.
    db = SessionLocal()
    course_id = db.execute(select(Course.id).where(Course.slug == COURSE_SLUG)).scalar_one()
    attempt = Attempt(course_id=course_id, viewer_id=uuid.uuid4(), shuffle_seed=1)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    attempt_id = str(attempt.public_id)
    db.close()

    for q in get_questions():
        answer(attempt_id, q["question_id"], q["correct_choice_id"])
    return attempt_id


def claim(attempt_id, name="Ada Lovelace"):
    return client.post(f"/api/v1/attempts/{attempt_id}/certificate", json={"recipient_name": name})


def test_claiming_on_a_passed_attempt_returns_a_code_and_the_name():
    attempt_id = start_and_pass_legacy_anonymous_attempt()
    response = claim(attempt_id, "Ada Lovelace")
    assert response.status_code == 200
    body = response.json()
    assert body["recipient_name"] == "Ada Lovelace"
    assert body["certificate_code"]
    assert body["course_title"] == "Course For Certificates"
    assert body["score"] == 5


def test_claiming_on_a_failed_attempt_returns_409():
    attempt_id = start_and_fail_attempt()
    response = claim(attempt_id)
    assert response.status_code == 409


def test_claiming_on_an_incomplete_attempt_returns_409():
    attempt_id = start_incomplete_attempt()
    response = claim(attempt_id)
    assert response.status_code == 409


def test_claiming_twice_keeps_the_original_code_and_updates_the_name():
    attempt_id = start_and_pass_legacy_anonymous_attempt()
    first = claim(attempt_id, "Ada Lovelace")
    second = claim(attempt_id, "Grace Hopper")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["certificate_code"] == second.json()["certificate_code"]
    assert second.json()["recipient_name"] == "Grace Hopper"


def test_empty_or_whitespace_only_name_returns_422():
    attempt_id = start_and_pass_attempt()
    assert claim(attempt_id, "").status_code == 422
    assert claim(attempt_id, "   ").status_code == 422


def test_pdf_endpoint_returns_a_pdf():
    attempt_id = start_and_pass_attempt()
    claim(attempt_id)

    response = client.get(f"/api/v1/attempts/{attempt_id}/certificate.pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_pdf_endpoint_before_claiming_returns_409():
    attempt_id = start_and_pass_attempt()
    response = client.get(f"/api/v1/attempts/{attempt_id}/certificate.pdf")
    assert response.status_code == 409


def test_verifying_a_real_code_returns_valid_true_with_course_and_score():
    attempt_id = start_and_pass_attempt()
    code = claim(attempt_id).json()["certificate_code"]

    response = client.get(f"/api/v1/certificates/{code}")
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["course_title"] == "Course For Certificates"
    assert body["score"] == 5


def test_verifying_an_unknown_code_returns_200_with_valid_false():
    response = client.get("/api/v1/certificates/ZZZZ-ZZZZ-ZZZZ")
    assert response.status_code == 200
    assert response.json()["valid"] is False


def test_verifying_is_case_insensitive_and_tolerates_missing_hyphens():
    attempt_id = start_and_pass_attempt()
    code = claim(attempt_id).json()["certificate_code"]

    lowercase_response = client.get(f"/api/v1/certificates/{code.lower()}")
    assert lowercase_response.status_code == 200
    assert lowercase_response.json()["valid"] is True

    unhyphenated_response = client.get(f"/api/v1/certificates/{code.replace('-', '')}")
    assert unhyphenated_response.status_code == 200
    assert unhyphenated_response.json()["valid"] is True


def test_verifying_an_anonymous_certificate_reports_not_an_account_holder():
    attempt_id = start_and_pass_legacy_anonymous_attempt()
    code = claim(attempt_id, "Ada Lovelace").json()["certificate_code"]

    response = client.get(f"/api/v1/certificates/{code}")
    assert response.json()["is_account_holder"] is False


def test_claiming_while_signed_in_uses_the_account_display_name_without_a_body_name():
    client.post(
        "/api/v1/auth/register",
        json={
            "email": SIGNED_IN_EMAIL,
            "password": SIGNED_IN_PASSWORD,
            "display_name": SIGNED_IN_DISPLAY_NAME,
        },
    )

    attempt_id = start_and_pass_attempt()
    response = client.post(f"/api/v1/attempts/{attempt_id}/certificate", json={})
    assert response.status_code == 200
    assert response.json()["recipient_name"] == SIGNED_IN_DISPLAY_NAME

    verify_response = client.get(f"/api/v1/certificates/{response.json()['certificate_code']}")
    assert verify_response.json()["is_account_holder"] is True


def test_claiming_while_signed_in_ignores_any_name_sent_in_the_body():
    client.post(
        "/api/v1/auth/register",
        json={
            "email": SIGNED_IN_EMAIL,
            "password": SIGNED_IN_PASSWORD,
            "display_name": SIGNED_IN_DISPLAY_NAME,
        },
    )

    attempt_id = start_and_pass_attempt()
    response = claim(attempt_id, "Someone Else Entirely")
    assert response.status_code == 200
    assert response.json()["recipient_name"] == SIGNED_IN_DISPLAY_NAME


def _get_attempt(attempt_id):
    db = SessionLocal()
    attempt = db.execute(select(Attempt).where(Attempt.public_id == uuid.UUID(attempt_id))).scalar_one()
    db.expunge(attempt)
    db.close()
    return attempt


def extract_pdf_text(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    return "\n".join(page.extract_text() for page in reader.pages)


def test_claiming_writes_a_snapshot_matching_the_course_at_that_moment():
    attempt_id = start_and_pass_attempt()
    claim(attempt_id)

    attempt = _get_attempt(attempt_id)
    assert attempt.cert_course_title == "Course For Certificates"
    assert attempt.cert_field_of_study == COURSE_FIELD_OF_STUDY
    assert attempt.cert_delivery_method == DELIVERY_METHOD_SELF_STUDY
    assert attempt.cert_credit_award == COURSE_CREDIT_AWARD
    assert attempt.cert_question_count == 5
    assert attempt.cert_sponsor_name == SPONSOR_NAME
    assert attempt.cert_sponsor_registry_id == SPONSOR_REGISTRY_ID
    assert attempt.cert_sponsor_state_registry_ids == SPONSOR_STATE_REGISTRY_IDS
    assert attempt.cert_issued_at is not None


def test_editing_the_course_after_claiming_changes_neither_the_pdf_nor_the_verification_page():
    attempt_id = start_and_pass_attempt()
    code = claim(attempt_id).json()["certificate_code"]

    db = SessionLocal()
    course = db.execute(select(Course).where(Course.slug == COURSE_SLUG)).scalar_one()
    course.title = "A Totally Different Course Title"
    course.field_of_study = "Taxes"
    course.credit_award = Decimal("3.0")
    db.commit()
    db.close()

    verify = client.get(f"/api/v1/certificates/{code}").json()
    assert verify["course_title"] == "Course For Certificates"
    assert verify["field_of_study"] == COURSE_FIELD_OF_STUDY
    assert Decimal(str(verify["credit_award"])) == COURSE_CREDIT_AWARD

    pdf_response = client.get(f"/api/v1/attempts/{attempt_id}/certificate.pdf")
    text = extract_pdf_text(pdf_response.content)
    assert "Course For Certificates" in text
    assert "A Totally Different Course Title" not in text


def test_claiming_twice_keeps_the_original_snapshot_even_if_the_course_changes_between_claims():
    attempt_id = start_and_pass_legacy_anonymous_attempt()
    first = claim(attempt_id, "Ada Lovelace").json()

    db = SessionLocal()
    course = db.execute(select(Course).where(Course.slug == COURSE_SLUG)).scalar_one()
    course.credit_award = Decimal("4.0")
    db.commit()
    db.close()

    second = claim(attempt_id, "Grace Hopper").json()
    assert second["certificate_code"] == first["certificate_code"]
    assert Decimal(str(second["credit_award"])) == COURSE_CREDIT_AWARD
    assert second["recipient_name"] == "Grace Hopper"


def test_pdf_contains_every_required_section_9_field():
    attempt_id = start_and_pass_attempt()
    claim(attempt_id)

    response = client.get(f"/api/v1/attempts/{attempt_id}/certificate.pdf")
    text = extract_pdf_text(response.content)

    assert "Certificates Flow User" in text  # participant name
    assert "Course For Certificates" in text  # course title
    assert SPONSOR_NAME in text
    assert SPONSOR_REGISTRY_ID in text
    assert SPONSOR_STATE_REGISTRY_IDS in text
    assert COURSE_FIELD_OF_STUDY in text
    assert DELIVERY_METHOD_SELF_STUDY in text
    assert "1.2" in text
    assert "50-minute" in text


def test_legacy_certificate_without_a_snapshot_still_renders_from_the_live_course():
    attempt_id = start_and_pass_legacy_anonymous_attempt()
    code = claim(attempt_id, "Ada Lovelace").json()["certificate_code"]

    # Simulate a pre-024 certificate: claimed before this feature shipped,
    # so it never had a snapshot written.
    db = SessionLocal()
    db.execute(
        update(Attempt)
        .where(Attempt.public_id == uuid.UUID(attempt_id))
        .values(
            cert_course_title=None,
            cert_field_of_study=None,
            cert_delivery_method=None,
            cert_credit_award=None,
            cert_question_count=None,
            cert_sponsor_name=None,
            cert_sponsor_registry_id=None,
            cert_sponsor_state_registry_ids=None,
            cert_issued_at=None,
        )
    )
    db.commit()
    db.close()

    pdf_response = client.get(f"/api/v1/attempts/{attempt_id}/certificate.pdf")
    assert pdf_response.status_code == 200
    assert pdf_response.content.startswith(b"%PDF")

    verify = client.get(f"/api/v1/certificates/{code}").json()
    assert verify["valid"] is True
    assert verify["course_title"] == "Course For Certificates"
    assert verify["sponsor_name"] == SPONSOR_NAME


def test_a_long_name_long_course_title_and_long_sponsor_name_all_still_fit():
    long_title = "A" + " Very Long Course Title About Something Complicated" * 4
    long_name = "Reginald Archibald Featherstonehaugh-Worthington the Third, CPA"
    long_sponsor = "The Extremely Long Sponsor Organization Name for Continuing Professional Education, Incorporated"

    db = SessionLocal()
    course = db.execute(select(Course).where(Course.slug == COURSE_SLUG)).scalar_one()
    course.title = long_title
    db.execute(update(SponsorProfile).where(SponsorProfile.id == 1).values(name=long_sponsor))
    db.commit()
    db.close()

    attempt_id = start_and_pass_legacy_anonymous_attempt()
    claim(attempt_id, long_name)

    response = client.get(f"/api/v1/attempts/{attempt_id}/certificate.pdf")
    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")

    text = extract_pdf_text(response.content)
    assert long_sponsor in text
