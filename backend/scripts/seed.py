from sqlalchemy import select

from app.db import SessionLocal
from app.models.choice import Choice
from app.models.lesson import Lesson
from app.models.question import Question
from app.services.quiz import validate_question

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

QUESTIONS = {
    "intro-to-ratios": [
        {
            "prompt": "A ratio compares which of the following?",
            "choices": [
                "Two or more quantities",
                "A single quantity to itself",
                "Only percentages",
                "Only whole numbers greater than ten",
            ],
            "correct_index": 0,
        },
        {
            "prompt": "A recipe uses 2 cups of flour for every 3 cups of sugar. "
            "What is the flour-to-sugar ratio?",
            "choices": ["3:2", "2:3", "1:1", "5:1"],
            "correct_index": 1,
        },
        {
            "prompt": "Which ratio is equivalent to 4:6?",
            "choices": ["1:2", "2:3", "3:4", "6:4"],
            "correct_index": 1,
        },
        {
            "prompt": "On a map, 1 inch represents 10 miles. This is an example of what?",
            "choices": [
                "A ratio used as a scale",
                "A ratio used as a percentage",
                "An unrelated pair of numbers",
                "A fraction with no real meaning",
            ],
            "correct_index": 0,
        },
        {
            "prompt": "To simplify the ratio 12:18, you should:",
            "choices": [
                "Add 6 to both sides",
                "Multiply both sides by 2",
                "Divide both sides by their greatest common factor",
                "Subtract 12 from both sides",
            ],
            "correct_index": 2,
        },
    ],
    "reading-a-balance-sheet": [
        {
            "prompt": "A balance sheet reports a company's financial position at:",
            "choices": [
                "A single point in time",
                "The end of a decade only",
                "Over a rolling ten year average",
                "The moment the company was founded",
            ],
            "correct_index": 0,
        },
        {
            "prompt": "Which of these is a liability?",
            "choices": ["Cash on hand", "Accounts payable", "Equipment owned", "Retained earnings"],
            "correct_index": 1,
        },
        {
            "prompt": "The basic accounting equation is:",
            "choices": [
                "Assets = Liabilities + Equity",
                "Assets = Revenue - Expenses",
                "Equity = Liabilities - Assets",
                "Liabilities = Assets + Equity",
            ],
            "correct_index": 0,
        },
        {
            "prompt": "Which of these is classified as an asset?",
            "choices": ["Accounts payable", "A bank loan owed", "Inventory", "Owner's equity"],
            "correct_index": 2,
        },
        {
            "prompt": "Equity represents:",
            "choices": [
                "What the company owes to suppliers",
                "The owners' residual claim after liabilities are subtracted from assets",
                "Total revenue for the year",
                "Cash held in a savings account",
            ],
            "correct_index": 1,
        },
    ],
    "the-water-cycle": [
        {
            "prompt": "Evaporation is the process by which:",
            "choices": [
                "Liquid water turns into water vapor",
                "Water vapor turns into ice",
                "Rain falls to the ground",
                "Rivers flow into the ocean",
            ],
            "correct_index": 0,
        },
        {
            "prompt": "Condensation occurs when water vapor:",
            "choices": [
                "Freezes into a solid",
                "Cools and turns back into liquid droplets",
                "Sinks underground",
                "Evaporates from the ocean",
            ],
            "correct_index": 1,
        },
        {
            "prompt": "Precipitation includes which of the following?",
            "choices": [
                "Evaporation and condensation only",
                "Rain, snow, sleet, and hail",
                "Only ocean currents",
                "Groundwater absorption"],
            "correct_index": 1,
        },
        {
            "prompt": "What powers the water cycle's evaporation stage?",
            "choices": [
                "Heat energy from the sun",
                "Wind speed alone",
                "Gravity pulling water downward",
                "Ocean salinity"],
            "correct_index": 0,
        },
        {
            "prompt": "After precipitation falls, water that soaks into the ground becomes:",
            "choices": ["Water vapor", "Groundwater", "A cloud", "Sleet"],
            "correct_index": 1,
        },
    ],
}


def seed_lessons(db):
    lessons_by_slug = {}
    for data in LESSONS:
        existing = db.execute(
            select(Lesson).where(Lesson.slug == data["slug"])
        ).scalar_one_or_none()
        if existing is not None:
            print(f"skipped (already exists): {data['slug']}")
            lessons_by_slug[data["slug"]] = existing
            continue
        lesson = Lesson(**data)
        db.add(lesson)
        db.flush()
        print(f"created: {data['slug']}")
        lessons_by_slug[data["slug"]] = lesson
    return lessons_by_slug


def seed_questions(db, lessons_by_slug):
    created_count = 0
    skipped_count = 0
    for slug, questions in QUESTIONS.items():
        lesson = lessons_by_slug[slug]
        for position, question_data in enumerate(questions, start=1):
            existing = db.execute(
                select(Question).where(
                    Question.lesson_id == lesson.id, Question.position == position
                )
            ).scalar_one_or_none()
            if existing is not None:
                skipped_count += 1
                continue

            question = Question(
                lesson_id=lesson.id,
                prompt=question_data["prompt"],
                position=position,
            )
            question.choices = [
                Choice(
                    text=choice_text,
                    is_correct=(index == question_data["correct_index"]),
                    position=index + 1,
                )
                for index, choice_text in enumerate(question_data["choices"])
            ]
            validate_question(question)
            db.add(question)
            created_count += 1
    return created_count, skipped_count


def seed():
    db = SessionLocal()
    try:
        lessons_by_slug = seed_lessons(db)
        created_count, skipped_count = seed_questions(db, lessons_by_slug)
        db.commit()
        print(f"questions created: {created_count}, questions skipped: {skipped_count}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
