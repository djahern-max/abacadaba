from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db import SessionLocal
from app.main import app
from app.models.course import Course
from app.models.session import Session as SessionModel
from app.models.user import User

client = TestClient(app)

SLUG_PREFIX = "test-currency"
ADMIN_EMAIL = "admin-currency@example.com"
MEMBER_EMAIL = "member-currency@example.com"
PASSWORD = "correct-horse-battery"

NOW = datetime.now(timezone.utc)
TODAY = NOW.date()


@pytest.fixture(autouse=True)
def cleanup():
    client.cookies.clear()
    yield
    client.cookies.clear()
    db = SessionLocal()
    emails = [ADMIN_EMAIL, MEMBER_EMAIL]
    user_ids = select(User.id).where(User.email.in_(emails))
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


def make_course(slug_suffix, **fields):
    db = SessionLocal()
    course = Course(
        slug=f"{SLUG_PREFIX}-{slug_suffix}",
        title=f"Currency Test Course {slug_suffix}",
        description="d",
        **fields,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    course_id = course.id
    db.close()
    return course_id


def get_dashboard():
    response = client.get("/api/v1/admin/currency")
    assert response.status_code == 200, response.text
    return response.json()


def test_currency_endpoint_requires_admin():
    assert client.get("/api/v1/admin/currency").status_code == 401

    register_and_login(MEMBER_EMAIL, is_admin=False)
    assert client.get("/api/v1/admin/currency").status_code == 403


def test_annual_course_reviewed_13_months_ago_is_overdue():
    login_admin()
    make_course("annual-13mo", reviewed_at=NOW - timedelta(days=396), review_cycle="annual")

    dashboard = get_dashboard()
    slugs = {row["title"] for row in dashboard["overdue_review"]}
    assert "Currency Test Course annual-13mo" in slugs


def test_annual_course_reviewed_6_months_ago_is_not_overdue():
    login_admin()
    make_course("annual-6mo", reviewed_at=NOW - timedelta(days=182), review_cycle="annual")

    dashboard = get_dashboard()
    titles = {row["title"] for row in dashboard["overdue_review"]} | {
        row["title"] for row in dashboard["due_soon"]
    }
    assert "Currency Test Course annual-6mo" not in titles


def test_biennial_course_reviewed_13_months_ago_is_not_overdue():
    login_admin()
    make_course("biennial-13mo", reviewed_at=NOW - timedelta(days=396), review_cycle="biennial")

    dashboard = get_dashboard()
    titles = {row["title"] for row in dashboard["overdue_review"]}
    assert "Currency Test Course biennial-13mo" not in titles


def test_annual_course_due_within_60_days_appears_in_due_soon_not_overdue():
    login_admin()
    # 365 - 335 = 30 days remaining, inside the 60-day due-soon window.
    make_course("annual-due-soon", reviewed_at=NOW - timedelta(days=335), review_cycle="annual")

    dashboard = get_dashboard()
    overdue_titles = {row["title"] for row in dashboard["overdue_review"]}
    due_soon_titles = {row["title"] for row in dashboard["due_soon"]}
    assert "Currency Test Course annual-due-soon" not in overdue_titles
    assert "Currency Test Course annual-due-soon" in due_soon_titles


def test_published_course_edited_after_review_appears_in_published_but_edited():
    login_admin()
    make_course("pub-edited", reviewed_at=NOW - timedelta(days=10), is_published=True)
    # content_updated_at server-defaults to now() at insert time, which is
    # after the reviewed_at set above - exactly the "edited after review"
    # state this section reports on.

    dashboard = get_dashboard()
    titles = {row["title"] for row in dashboard["published_but_edited"]}
    assert "Currency Test Course pub-edited" in titles


def test_unpublished_course_edited_after_review_does_not_appear_in_published_but_edited():
    login_admin()
    make_course("draft-edited", reviewed_at=NOW - timedelta(days=10), is_published=False)

    dashboard = get_dashboard()
    titles = {row["title"] for row in dashboard["published_but_edited"]}
    assert "Currency Test Course draft-edited" not in titles


def test_course_expiring_within_60_days_appears_in_expired_or_expiring():
    login_admin()
    make_course("expiring-soon", expires_on=TODAY + timedelta(days=30))

    dashboard = get_dashboard()
    titles = {row["title"] for row in dashboard["expired_or_expiring"]}
    assert "Currency Test Course expiring-soon" in titles


def test_course_already_expired_sorts_before_a_course_merely_expiring_soon():
    login_admin()
    make_course("expired-already", expires_on=TODAY - timedelta(days=5))
    make_course("expiring-later", expires_on=TODAY + timedelta(days=45))

    dashboard = get_dashboard()
    titles_in_order = [row["title"] for row in dashboard["expired_or_expiring"]]
    already = titles_in_order.index("Currency Test Course expired-already")
    later = titles_in_order.index("Currency Test Course expiring-later")
    assert already < later


def test_course_qualifying_for_two_sections_appears_in_both():
    login_admin()
    make_course(
        "double-trouble",
        reviewed_at=NOW - timedelta(days=400),
        review_cycle="annual",
        expires_on=TODAY - timedelta(days=1),
        is_published=True,
    )

    dashboard = get_dashboard()
    overdue_titles = {row["title"] for row in dashboard["overdue_review"]}
    expired_titles = {row["title"] for row in dashboard["expired_or_expiring"]}
    assert "Currency Test Course double-trouble" in overdue_titles
    assert "Currency Test Course double-trouble" in expired_titles


def test_course_with_no_review_or_expiration_appears_nowhere():
    login_admin()
    make_course("untouched")

    dashboard = get_dashboard()
    for section in dashboard.values():
        assert all("untouched" not in row["title"] for row in section)
