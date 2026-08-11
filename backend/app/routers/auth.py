import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.dependencies import get_viewer_id, require_user
from app.middleware.viewer import VIEWER_COOKIE_LIFETIME_DAYS, VIEWER_COOKIE_NAME
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, UserPublic
from app.services import auth as auth_service
from app.services import google_auth
from app.services import watch as watch_service
from app.services.auth import SESSION_COOKIE_NAME, SESSION_LIFETIME_DAYS

router = APIRouter(prefix="/auth")

GOOGLE_STATE_COOKIE_NAME = "google_oauth_state"
GOOGLE_STATE_LIFETIME_SECONDS = 10 * 60


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


def _rotate_viewer_id_cookie(response: Response) -> None:
    # Defence in depth: even if some future query reintroduces a
    # viewer-based match, the cookie no longer points at the previous
    # person's row once they sign out.
    response.set_cookie(
        key=VIEWER_COOKIE_NAME,
        value=str(uuid.uuid4()),
        max_age=VIEWER_COOKIE_LIFETIME_DAYS * 24 * 60 * 60,
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
        domain=settings.session_cookie_domain,
        path="/",
    )


def _set_state_cookie(response: Response, state: str) -> None:
    response.set_cookie(
        key=GOOGLE_STATE_COOKIE_NAME,
        value=state,
        max_age=GOOGLE_STATE_LIFETIME_SECONDS,
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
        path="/",
    )


def _google_configured() -> bool:
    return bool(settings.google_client_id and settings.google_client_secret and settings.google_redirect_uri)


@router.post("/register", response_model=UserPublic, status_code=201)
def register(
    payload: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
    viewer_id: uuid.UUID = Depends(get_viewer_id),
):
    try:
        user = auth_service.register(db, payload.email, payload.password, payload.display_name)
    except auth_service.EmailTakenError as exc:
        raise HTTPException(status_code=409, detail="That email is already registered") from exc

    watch_service.claim_anonymous_progress(db, viewer_id, user)

    session = auth_service.create_session(db, user)
    _set_session_cookie(response, session.id)
    return user


@router.post("/login", response_model=UserPublic)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    viewer_id: uuid.UUID = Depends(get_viewer_id),
):
    auth_service.purge_expired_sessions(db)
    user = auth_service.authenticate(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    watch_service.claim_anonymous_progress(db, viewer_id, user)

    session = auth_service.create_session(db, user)
    _set_session_cookie(response, session.id)
    return user


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token is not None:
        auth_service.delete_session(db, token)
    response.delete_cookie(key=SESSION_COOKIE_NAME, domain=settings.session_cookie_domain, path="/")
    _rotate_viewer_id_cookie(response)


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(require_user)):
    return user


@router.get("/google/start")
def google_start():
    if not _google_configured():
        raise HTTPException(status_code=404)

    state = secrets.token_urlsafe(32)
    authorization_url = google_auth.build_authorization_url(state)
    redirect = RedirectResponse(url=authorization_url, status_code=302)
    _set_state_cookie(redirect, state)
    return redirect


@router.get("/google/callback")
def google_callback(request: Request, db: Session = Depends(get_db)):
    def failure(error_code: str) -> RedirectResponse:
        redirect = RedirectResponse(url=f"{settings.site_url}/login?error={error_code}", status_code=302)
        redirect.delete_cookie(key=GOOGLE_STATE_COOKIE_NAME, path="/")
        return redirect

    code = request.query_params.get("code")
    state = request.query_params.get("state")
    cookie_state = request.cookies.get(GOOGLE_STATE_COOKIE_NAME)

    if not code or not state or not cookie_state or state != cookie_state:
        return failure("state_mismatch")

    try:
        identity = google_auth.exchange_code(code)
    except google_auth.GoogleAuthError:
        return failure("google_auth_failed")

    try:
        user = google_auth.find_or_create_user(db, identity)
    except google_auth.UnverifiedEmailError:
        return failure("unverified_email")

    watch_service.claim_anonymous_progress(db, get_viewer_id(request), user)

    session = auth_service.create_session(db, user)
    redirect = RedirectResponse(url=settings.site_url, status_code=302)
    _set_session_cookie(redirect, session.id)
    redirect.delete_cookie(key=GOOGLE_STATE_COOKIE_NAME, path="/")
    return redirect
