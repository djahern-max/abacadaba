import secrets
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DbSession

from app.models.session import Session as SessionModel
from app.models.user import User

SESSION_LIFETIME_DAYS = 30
SESSION_COOKIE_NAME = "session_id"

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hashed once at import time so authenticate() always pays the bcrypt cost,
# even for an email that doesn't exist, keeping response timing uniform.
_DUMMY_HASH = _pwd_context.hash(secrets.token_urlsafe(32))


class EmailTakenError(Exception):
    """Raised when registering with an email that is already in use."""


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def register(db: DbSession, email: str, password: str, display_name: str) -> User:
    normalized_email = email.strip().lower()
    existing = db.execute(select(User).where(User.email == normalized_email)).scalar_one_or_none()
    if existing is not None:
        raise EmailTakenError(f"{normalized_email} is already registered")

    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
        display_name=display_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: DbSession, email: str, password: str) -> User | None:
    normalized_email = email.strip().lower()
    user = db.execute(select(User).where(User.email == normalized_email)).scalar_one_or_none()

    if user is None or user.password_hash is None:
        verify_password(password, _DUMMY_HASH)
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def purge_expired_sessions(db: DbSession) -> None:
    db.execute(delete(SessionModel).where(SessionModel.expires_at < datetime.now(timezone.utc)))
    db.commit()


def create_session(db: DbSession, user: User) -> SessionModel:
    session = SessionModel(
        id=secrets.token_urlsafe(32),
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=SESSION_LIFETIME_DAYS),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session_user(db: DbSession, token: str) -> User | None:
    session = db.execute(select(SessionModel).where(SessionModel.id == token)).scalar_one_or_none()
    if session is None:
        return None
    if session.expires_at < datetime.now(timezone.utc):
        return None

    return db.execute(select(User).where(User.id == session.user_id)).scalar_one_or_none()


def delete_session(db: DbSession, token: str) -> None:
    db.execute(delete(SessionModel).where(SessionModel.id == token))
    db.commit()
