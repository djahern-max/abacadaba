from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.dependencies import require_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, UserPublic
from app.services import auth as auth_service
from app.services.auth import SESSION_COOKIE_NAME, SESSION_LIFETIME_DAYS

router = APIRouter(prefix="/auth")


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_LIFETIME_DAYS * 24 * 60 * 60,
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
        domain=settings.session_cookie_domain,
        path="/",
    )


@router.post("/register", response_model=UserPublic, status_code=201)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    try:
        user = auth_service.register(db, payload.email, payload.password, payload.display_name)
    except auth_service.EmailTakenError as exc:
        raise HTTPException(status_code=409, detail="That email is already registered") from exc

    session = auth_service.create_session(db, user)
    _set_session_cookie(response, session.id)
    return user


@router.post("/login", response_model=UserPublic)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    auth_service.purge_expired_sessions(db)
    user = auth_service.authenticate(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    session = auth_service.create_session(db, user)
    _set_session_cookie(response, session.id)
    return user


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token is not None:
        auth_service.delete_session(db, token)
    response.delete_cookie(key=SESSION_COOKIE_NAME, domain=settings.session_cookie_domain, path="/")


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(require_user)):
    return user
