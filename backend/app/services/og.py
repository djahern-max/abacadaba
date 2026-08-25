"""Server-rendered Open Graph previews for shared links.

Apple's link-preview fetcher (and most others) never runs JavaScript, so
meta tags set from React are invisible to it - see current-feature.md,
Part 5. This module builds the static, meta-only HTML a crawler needs.
abacadaba.conf's commented-out "Open Graph crawler branch" proxies
crawler User-Agents on /courses/{slug} here (internally, as
/api/v1/og/courses/{slug}) and lets everyone else fall through to the
SPA unchanged.
"""

import html

from sqlalchemy.orm import Session

from app.config import settings
from app.services import courses as courses_service
from app.services import storage

DEFAULT_IMAGE_PATH = "/og-default.png"
DEFAULT_DESCRIPTION = "Short CPE lessons you can actually finish."
DESCRIPTION_MAX_LENGTH = 200
THUMBNAIL_URL_EXPIRES_IN = 3600


def _truncate(text: str, limit: int) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    cut = collapsed[:limit].rsplit(" ", 1)[0]
    return f"{cut}…"


def _render(
    *,
    title: str,
    description: str,
    url: str,
    image: str,
    image_width: int | None = None,
    image_height: int | None = None,
) -> str:
    tags = [
        ("og:type", "website"),
        ("og:site_name", "abacadaba"),
        ("og:title", title),
        ("og:description", description),
        ("og:url", url),
        ("og:image", image),
    ]
    if image_width is not None:
        tags.append(("og:image:width", str(image_width)))
    if image_height is not None:
        tags.append(("og:image:height", str(image_height)))
    tags.append(("og:image:alt", title))

    meta_lines = "\n    ".join(
        f'<meta property="{name}" content="{html.escape(value, quote=True)}">' for name, value in tags
    )

    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "  <head>\n"
        '    <meta charset="UTF-8">\n'
        f"    <title>{html.escape(title)}</title>\n"
        f"    {meta_lines}\n"
        '    <meta name="twitter:card" content="summary_large_image">\n'
        "  </head>\n"
        "  <body></body>\n"
        "</html>\n"
    )


def default_preview_html() -> str:
    return _render(
        title="abacadaba",
        description=DEFAULT_DESCRIPTION,
        url=f"{settings.site_url}/",
        image=f"{settings.site_url}{DEFAULT_IMAGE_PATH}",
        image_width=1200,
        image_height=630,
    )


def course_preview_html(db: Session, slug: str) -> str:
    # get_by_slug already filters is_published=True (app/services/courses.py)
    # - the same query the public course endpoint uses, not a second one, so
    # this can't reopen the draft-leak bug current-feature.md warns about.
    course = courses_service.get_by_slug(db, slug)
    if course is None:
        return default_preview_html()

    image = f"{settings.site_url}{DEFAULT_IMAGE_PATH}"
    if course.thumbnail_key:
        try:
            image = storage.generate_presigned_get(course.thumbnail_key, expires_in=THUMBNAIL_URL_EXPIRES_IN)
        except storage.StorageError:
            image = f"{settings.site_url}{DEFAULT_IMAGE_PATH}"

    return _render(
        title=course.title,
        description=_truncate(course.description, DESCRIPTION_MAX_LENGTH),
        url=f"{settings.site_url}/courses/{course.slug}",
        image=image,
    )
