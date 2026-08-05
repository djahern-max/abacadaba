from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db import SessionLocal
from app.main import app
from app.models.session import Session as SessionModel
from app.models.user import User

client = TestClient(app)

TEST_EMAIL = "ada@example.com"
TEST_PASSWORD = "correct-horse-battery"
TEST_DISPLAY_NAME = "Ada Lovelace"


@pytest.fixture(autouse=True)
def clean_up_test_user():
    # TestClient keeps a cookie jar across requests; clear it so one test's
    # session cookie can't leak into the next test's "no cookie" assertions.
    client.cookies.clear()

    yield

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


def login(email=TEST_EMAIL, password=TEST_PASSWORD):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_registering_returns_201_and_sets_a_cookie():
    response = register()
    assert response.status_code == 201
    assert "session_id" in response.cookies
    body = response.json()
    assert body["email"] == TEST_EMAIL
    assert body["display_name"] == TEST_DISPLAY_NAME
    assert body["is_admin"] is False


def test_registering_a_duplicate_email_returns_409_case_insensitively():
    register()
    response = register(email=TEST_EMAIL.upper())
    assert response.status_code == 409


def test_a_short_password_returns_422():
    response = register(password="short")
    assert response.status_code == 422


def test_login_with_correct_credentials_returns_200_and_sets_a_cookie():
    register()
    response = login()
    assert response.status_code == 200
    assert "session_id" in response.cookies
    assert response.json()["email"] == TEST_EMAIL


def test_login_with_a_wrong_password_returns_401():
    register()
    response = login(password="wrong-password-entirely")
    assert response.status_code == 401


def test_me_without_a_cookie_returns_401():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_with_a_cookie_returns_the_user_and_never_includes_password_hash():
    register()
    login()

    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == TEST_EMAIL
    assert "password_hash" not in body
    assert "password_hash" not in response.text


def test_logout_clears_the_session_so_me_returns_401_afterward():
    register()
    login()

    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 204

    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 401


def test_an_expired_session_returns_401():
    register()
    login_response = login()
    cookie = login_response.cookies["session_id"]

    db = SessionLocal()
    session = db.get(SessionModel, cookie)
    session.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.commit()
    db.close()

    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
