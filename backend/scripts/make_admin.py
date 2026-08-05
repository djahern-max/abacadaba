import sys

from sqlalchemy import select

from app.db import SessionLocal
from app.models.user import User


def make_admin(email: str):
    normalized_email = email.strip().lower()
    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.email == normalized_email)).scalar_one_or_none()
        if user is None:
            print(f"No user registered with email {normalized_email}")
            sys.exit(1)

        user.is_admin = True
        db.commit()
        print(f"{normalized_email} is now an admin")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.make_admin <email>")
        sys.exit(1)
    make_admin(sys.argv[1])
