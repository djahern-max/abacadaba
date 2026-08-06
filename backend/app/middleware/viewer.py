import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import settings

VIEWER_COOKIE_NAME = "viewer_id"
VIEWER_COOKIE_LIFETIME_DAYS = 365


class ViewerIdentityMiddleware(BaseHTTPMiddleware):
    """Ensures every request carries a viewer_id, cookie-backed for anonymous
    visitors. Runs before routing so no route has to remember to do this."""

    async def dispatch(self, request: Request, call_next):
        cookie_value = request.cookies.get(VIEWER_COOKIE_NAME)
        try:
            viewer_id = uuid.UUID(cookie_value) if cookie_value else uuid.uuid4()
        except ValueError:
            viewer_id = uuid.uuid4()
        needs_cookie = cookie_value != str(viewer_id)

        request.state.viewer_id = viewer_id
        response = await call_next(request)

        if needs_cookie:
            response.set_cookie(
                key=VIEWER_COOKIE_NAME,
                value=str(viewer_id),
                max_age=VIEWER_COOKIE_LIFETIME_DAYS * 24 * 60 * 60,
                httponly=True,
                samesite="lax",
                secure=settings.session_cookie_secure,
                domain=settings.session_cookie_domain,
                path="/",
            )
        return response
