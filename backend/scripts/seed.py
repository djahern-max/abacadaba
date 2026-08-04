from sqlalchemy import select

from app.db import SessionLocal
from app.models.lesson import Lesson

LESSONS = [
    {
        "slug": "intro-to-ratios",
        "title": "Intro to Ratios",
        "description": (
            "Learn what a ratio is and how it compares two quantities. "
            "We'll walk through everyday examples like recipes and maps. "
            "By the end you'll be able to simplify and scale ratios confidently."
        ),
        "duration_seconds": 310,
        "is_published": True,
    },
    {
        "slug": "reading-a-balance-sheet",
        "title": "Reading a Balance Sheet",
        "description": (
            "A quick tour of assets, liabilities, and equity. "
            "See how the balance sheet fits together with a real company example. "
            "Great primer before diving into other financial statements."
        ),
        "duration_seconds": 295,
        "is_published": True,
    },
    {
        "slug": "the-water-cycle",
        "title": "The Water Cycle",
        "description": (
            "Follow a single drop of water through evaporation, condensation, "
            "and precipitation. We'll cover why the cycle matters for weather "
            "and climate along the way."
        ),
        "duration_seconds": 300,
        "is_published": True,
    },
]


def seed():
    db = SessionLocal()
    try:
        for data in LESSONS:
            existing = db.execute(
                select(Lesson).where(Lesson.slug == data["slug"])
            ).scalar_one_or_none()
            if existing is not None:
                print(f"skipped (already exists): {data['slug']}")
                continue
            db.add(Lesson(**data))
            print(f"created: {data['slug']}")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
