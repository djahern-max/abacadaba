from sqlalchemy.orm import Session

from app.models.sponsor_profile import SponsorProfile

# What a compliant certificate actually needs printed on it (9.01 items 1
# and 8) - not the whole identity record. state_registry_ids is correctly
# left out: it's "if required by the state boards", so a sponsor with none
# is still complete. website/contact_email/address are part of the identity
# record an admin edits but never appear on a certificate, so they don't
# block publish either.
REQUIRED_FIELDS = ["name", "national_registry_id"]

FIELD_LABELS = {
    "name": "sponsor name",
    "national_registry_id": "NASBA sponsor registry ID",
}


def get_sponsor_profile(db: Session) -> SponsorProfile:
    # Always present - the migration that created this table seeded row id
    # 1, and the singleton CHECK means nothing can ever delete or duplicate
    # it through this application.
    return db.get(SponsorProfile, 1)


def missing_fields(profile: SponsorProfile) -> list[str]:
    return [FIELD_LABELS[field] for field in REQUIRED_FIELDS if not getattr(profile, field).strip()]


def update_sponsor_profile(db: Session, updates: dict) -> SponsorProfile:
    profile = get_sponsor_profile(db)
    for field, value in updates.items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile
