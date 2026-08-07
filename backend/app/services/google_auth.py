from dataclasses import dataclass

from authlib.integrations.httpx_client import OAuth2Client
from authlib.jose import JsonWebKey, jwt
from authlib.jose.errors import JoseError
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.config import settings
from app.models.user import User

AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
JWKS_ENDPOINT = "https://www.googleapis.com/oauth2/v3/certs"
ISSUERS = ["https://accounts.google.com", "accounts.google.com"]
SCOPE = "openid email profile"


class GoogleAuthError(Exception):
    """Raised when the authorization code or ID token cannot be exchanged or verified."""


class UnverifiedEmailError(Exception):
    """Raised when linking to an existing account would require an unverified Google email."""


@dataclass
class GoogleIdentity:
    sub: str
    email: str
    email_verified: bool
    name: str


def _client() -> OAuth2Client:
    return OAuth2Client(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        redirect_uri=settings.google_redirect_uri,
    )


def build_authorization_url(state: str) -> str:
    with _client() as client:
        url, _ = client.create_authorization_url(AUTHORIZATION_ENDPOINT, state=state, scope=SCOPE)
    return url


def exchange_code(code: str) -> GoogleIdentity:
    try:
        with _client() as client:
            token = client.fetch_token(TOKEN_ENDPOINT, code=code, grant_type="authorization_code")
            id_token = token.get("id_token")
            if id_token is None:
                raise GoogleAuthError("Google did not return an ID token")
            jwks = client.get(JWKS_ENDPOINT).json()
    except GoogleAuthError:
        raise
    except Exception as exc:
        raise GoogleAuthError("Failed to exchange the authorization code with Google") from exc

    try:
        key_set = JsonWebKey.import_key_set(jwks)
        claims = jwt.decode(
            id_token,
            key_set,
            claims_options={
                "iss": {"values": ISSUERS},
                "aud": {"value": settings.google_client_id},
            },
        )
        claims.validate()
    except JoseError as exc:
        raise GoogleAuthError("Failed to verify Google's ID token") from exc

    return GoogleIdentity(
        sub=claims["sub"],
        email=claims["email"],
        email_verified=bool(claims.get("email_verified", False)),
        name=claims.get("name") or claims["email"],
    )


def find_or_create_user(db: DbSession, identity: GoogleIdentity) -> User:
    user = db.execute(select(User).where(User.google_sub == identity.sub)).scalar_one_or_none()
    if user is not None:
        return user

    normalized_email = identity.email.strip().lower()
    user = db.execute(select(User).where(User.email == normalized_email)).scalar_one_or_none()
    if user is not None:
        if not identity.email_verified:
            raise UnverifiedEmailError(
                f"{normalized_email} is not verified by Google and cannot be linked automatically"
            )
        user.google_sub = identity.sub
        db.commit()
        db.refresh(user)
        return user

    user = User(
        email=normalized_email,
        password_hash=None,
        google_sub=identity.sub,
        display_name=identity.name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
