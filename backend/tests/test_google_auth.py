import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.models.session import Session as SessionModel
from app.models.user import User
from app.services import auth as auth_service
from app.services import google_auth

client = TestClient(app, follow_redirects=False)

TEST_EMAIL = "grace@example.com"
TEST_PASSWORD = "correct-horse-battery"
TEST_DISPLAY_NAME = "Grace Hopper"
GOOGLE_SUB = "1234567890"


def make_identity(sub=GOOGLE_SUB, email=TEST_EMAIL, email_verified=True, name=TEST_DISPLAY_NAME):
    return google_auth.GoogleIdentity(sub=sub, email=email, email_verified=email_verified, name=name)


@pytest.fixture(autouse=True)
def configure_google(monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "test-client-id")
    monkeypatch.setattr(settings, "google_client_secret", "test-client-secret")
    monkeypatch.setattr(settings, "google_redirect_uri", "http://localhost:8000/api/v1/auth/google/callback")


@pytest.fixture(autouse=True)
def clean_up_test_user():
    client.cookies.clear()

    yield

    client.cookies.clear()

    db = SessionLocal()
    user_ids = select(User.id).where(User.email == TEST_EMAIL)
    db.execute(delete(SessionModel).where(SessionModel.user_id.in_(user_ids)))
    db.execute(delete(User).where(User.email == TEST_EMAIL))
    db.commit()
    db.close()


def register(email=TEST_EMAIL, password=TEST_PASSWORD, display_name=TEST_DISPLAY_NAME):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": display_name},
    )


def run_google_login(monkeypatch, identity):
    monkeypatch.setattr(google_auth, "exchange_code", lambda code: identity)
    start_response = client.get("/api/v1/auth/google/start")
    assert start_response.status_code == 302
    state = start_response.cookies["google_oauth_state"]
    return client.get(
        "/api/v1/auth/google/callback",
        params={"code": "test-code", "state": state},
    )


def count_users_with_email(email=TEST_EMAIL):
    db = SessionLocal()
    count = db.execute(
        select(func.count()).select_from(User).where(User.email == email)
    ).scalar_one()
    db.close()
    return count


def test_a_new_google_identity_creates_a_user_with_no_password_and_signs_in(monkeypatch):
    response = run_google_login(monkeypatch, make_identity())

    assert response.status_code == 302
    assert "session_id" in response.cookies

    db = SessionLocal()
    user = db.execute(select(User).where(User.email == TEST_EMAIL)).scalar_one()
    assert user.password_hash is None
    assert user.google_sub == GOOGLE_SUB
    db.close()


def test_signing_in_twice_with_the_same_sub_reuses_the_account(monkeypatch):
    run_google_login(monkeypatch, make_identity())
    client.cookies.clear()
    run_google_login(monkeypatch, make_identity())

    assert count_users_with_email() == 1


def test_a_google_identity_links_to_an_existing_verified_password_account(monkeypatch):
    register()
    client.cookies.clear()

    response = run_google_login(monkeypatch, make_identity(email_verified=True))

    assert response.status_code == 302
    assert "session_id" in response.cookies
    assert count_users_with_email() == 1

    db = SessionLocal()
    user = db.execute(select(User).where(User.email == TEST_EMAIL)).scalar_one()
    assert user.google_sub == GOOGLE_SUB
    assert user.password_hash is not None
    db.close()


def test_an_unverified_email_is_refused_and_does_not_link(monkeypatch):
    register()
    client.cookies.clear()

    response = run_google_login(monkeypatch, make_identity(email_verified=False))

    assert response.status_code == 302
    assert response.headers["location"] == f"{settings.site_url}/login?error=unverified_email"
    assert "session_id" not in response.cookies
    assert count_users_with_email() == 1

    db = SessionLocal()
    user = db.execute(select(User).where(User.email == TEST_EMAIL)).scalar_one()
    assert user.google_sub is None
    db.close()


def test_a_state_mismatch_is_rejected(monkeypatch):
    monkeypatch.setattr(google_auth, "exchange_code", lambda code: make_identity())
    start_response = client.get("/api/v1/auth/google/start")
    assert start_response.status_code == 302

    response = client.get(
        "/api/v1/auth/google/callback",
        params={"code": "test-code", "state": "tampered-state-value"},
    )

    assert response.status_code == 302
    assert response.headers["location"] == f"{settings.site_url}/login?error=state_mismatch"
    assert "session_id" not in response.cookies


def test_password_login_against_a_google_only_account_returns_401_not_500(monkeypatch):
    run_google_login(monkeypatch, make_identity())
    client.cookies.clear()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": TEST_EMAIL, "password": "some-password-guess"},
    )

    assert response.status_code == 401


def test_google_start_returns_404_when_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", None)

    response = client.get("/api/v1/auth/google/start")

    assert response.status_code == 404
