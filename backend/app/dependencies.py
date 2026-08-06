import uuid

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User
from app.services.auth import SESSION_COOKIE_NAME, get_session_user


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token is None:
        return None
    return get_session_user(db, token)


def get_viewer_id(request: Request) -> uuid.UUID:
    # Set by ViewerIdentityMiddleware on every request, cookie-backed.
    return request.state.viewer_id


def require_user(user: User | None = Depends(get_current_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in required")
    return user


def require_admin(user: User | None = Depends(get_current_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in required")
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
