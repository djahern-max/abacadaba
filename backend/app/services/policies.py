from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.policies import PLACEHOLDER_BODY
from app.models.policy import Policy


class PolicyNotFoundError(Exception):
    """Raised when a slug does not match any of the four seeded policies."""


def is_placeholder(policy: Policy) -> bool:
    # Derived by comparing against the seeded constant, not stored as a flag
    # - see current-feature.md and app/services/admin_content.py's own
    # is_placeholder-style derivations (021, 022) for the same rule.
    return policy.body.strip() == PLACEHOLDER_BODY


def list_policies(db: Session) -> list[Policy]:
    return list(db.execute(select(Policy).order_by(Policy.slug)).scalars())


def get_policy(db: Session, slug: str) -> Policy:
    policy = db.execute(select(Policy).where(Policy.slug == slug)).scalar_one_or_none()
    if policy is None:
        raise PolicyNotFoundError(f"Policy '{slug}' not found")
    return policy


def update_policy(db: Session, slug: str, updates: dict) -> Policy:
    policy = get_policy(db, slug)
    for field, value in updates.items():
        setattr(policy, field, value)
    db.commit()
    db.refresh(policy)
    return policy


def placeholder_titles(db: Session) -> list[str]:
    """Titles of any of the four seeded policies still carrying the seeded
    placeholder text - what validate_for_publish names in its refusal."""
    return [policy.title for policy in list_policies(db) if is_placeholder(policy)]
