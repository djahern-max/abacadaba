import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select, update

from app.constants.policies import PLACEHOLDER_BODY, SEEDED_POLICIES
from app.db import SessionLocal
from app.main import app
from app.models.policy import Policy
from app.models.session import Session as SessionModel
from app.models.user import User

client = TestClient(app)

ADMIN_EMAIL = "admin-policies@example.com"
MEMBER_EMAIL = "member-policies@example.com"
PASSWORD = "correct-horse-battery"


@pytest.fixture(autouse=True)
def cleanup():
    client.cookies.clear()
    yield
    client.cookies.clear()
    db = SessionLocal()
    emails = [ADMIN_EMAIL, MEMBER_EMAIL]
    user_ids = select(User.id).where(User.email.in_(emails))
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


def test_seeded_slugs_all_render_for_a_signed_out_visitor():
    for slug, _title in SEEDED_POLICIES:
        response = client.get(f"/api/v1/policies/{slug}")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["slug"] == slug
        assert "body" in body and "title" in body


def test_list_policies_returns_all_four():
    response = client.get("/api/v1/policies")
    assert response.status_code == 200
    slugs = {policy["slug"] for policy in response.json()}
    assert slugs == {slug for slug, _title in SEEDED_POLICIES}


def test_unknown_slug_returns_404():
    response = client.get("/api/v1/policies/not-a-real-policy")
    assert response.status_code == 404


def test_fresh_seeded_policy_reports_is_placeholder_true():
    # conftest's autouse reset_policies fixture overwrites every policy's
    # body with real text before each test - reset this one back to what a
    # fresh database actually seeds, to test the seeded state itself.
    db = SessionLocal()
    db.execute(update(Policy).where(Policy.slug == "refund-and-cancellation").values(body=PLACEHOLDER_BODY))
    db.commit()
    db.close()

    response = client.get("/api/v1/policies/refund-and-cancellation")
    assert response.json()["is_placeholder"] is True


def test_admin_patch_updates_title_and_body():
    login_admin()
    response = client.patch(
        "/api/v1/admin/policies/complaint-resolution",
        json={"title": "How We Handle Complaints", "body": "Email support@example.com within 30 days."},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"] == "How We Handle Complaints"
    assert body["body"] == "Email support@example.com within 30 days."
    assert body["is_placeholder"] is False

    # Persisted, not just echoed back.
    refetched = client.get("/api/v1/policies/complaint-resolution")
    assert refetched.json()["body"] == "Email support@example.com within 30 days."


def test_admin_patch_requires_admin():
    assert client.patch("/api/v1/admin/policies/complaint-resolution", json={}).status_code == 401

    register_and_login(MEMBER_EMAIL, is_admin=False)
    assert client.patch("/api/v1/admin/policies/complaint-resolution", json={}).status_code == 403


def test_admin_patch_unknown_slug_returns_404():
    login_admin()
    response = client.patch("/api/v1/admin/policies/not-a-real-policy", json={"body": "x"})
    assert response.status_code == 404
