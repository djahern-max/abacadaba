from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lesson import Lesson


def list_published(db: Session) -> list[Lesson]:
    stmt = select(Lesson).where(Lesson.is_published.is_(True)).order_by(Lesson.id)
    return list(db.execute(stmt).scalars().all())


def get_by_slug(db: Session, slug: str) -> Lesson | None:
    stmt = select(Lesson).where(Lesson.slug == slug, Lesson.is_published.is_(True))
    return db.execute(stmt).scalar_one_or_none()
