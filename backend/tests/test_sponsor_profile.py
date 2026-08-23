import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db import SessionLocal
from app.main import app
from app.models.session import Session as SessionModel
from app.models.user import User

client = TestClient(app)

ADMIN_EMAIL = "admin-sponsor@example.com"
MEMBER_EMAIL = "member-sponsor@example.com"
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


def test_sponsor_endpoints_require_admin():
    assert client.get("/api/v1/admin/sponsor").status_code == 401
    assert client.patch("/api/v1/admin/sponsor", json={}).status_code == 401

    register_and_login(MEMBER_EMAIL, is_admin=False)
    assert client.get("/api/v1/admin/sponsor").status_code == 403
    assert client.patch("/api/v1/admin/sponsor", json={}).status_code == 403


def test_get_sponsor_returns_the_seeded_singleton():
    login_admin()
    response = client.get("/api/v1/admin/sponsor")
    assert response.status_code == 200
    body = response.json()
    assert "name" in body
    assert "national_registry_id" in body
    assert isinstance(body["missing_fields"], list)


def test_blank_profile_reports_missing_fields():
    login_admin()
    client.patch("/api/v1/admin/sponsor", json={"name": "", "national_registry_id": ""})
    response = client.get("/api/v1/admin/sponsor")
    missing = response.json()["missing_fields"]
    assert "sponsor name" in missing
    assert "NASBA sponsor registry ID" in missing


def test_patch_updates_only_the_fields_sent():
    login_admin()
    client.patch(
        "/api/v1/admin/sponsor",
        json={
            "name": "abacadaba U",
            "national_registry_id": "999888",
            "website": "https://abacadaba.example",
            "contact_email": "compliance@abacadaba.example",
            "address": "1 Learning Ln, Anytown, ST 00000",
        },
    )
    response = client.patch("/api/v1/admin/sponsor", json={"name": "abacadaba University"})
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "abacadaba University"
    assert body["national_registry_id"] == "999888"
    assert body["missing_fields"] == []


def test_state_registry_ids_is_optional_and_free_form():
    login_admin()
    client.patch("/api/v1/admin/sponsor", json={"name": "abacadaba", "national_registry_id": "1"})
    response = client.patch(
        "/api/v1/admin/sponsor", json={"state_registry_ids": "NH #123, TX #456"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["state_registry_ids"] == "NH #123, TX #456"
    # Not required - a sponsor with none is still complete.
    assert body["missing_fields"] == []
