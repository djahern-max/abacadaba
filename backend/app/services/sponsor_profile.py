from sqlalchemy.orm import Session

from app.constants.registry_status import REGISTRY_STATUS_REGISTERED
from app.models.sponsor_profile import SponsorProfile

# What a compliant certificate actually needs printed on it (9.01 items 1
# and 8) - not the whole identity record. state_registry_ids is correctly
# left out: it's "if required by the state boards", so a sponsor with none
# is still complete. website/contact_email/address are part of the identity
# record an admin edits but never appear on a certificate, so they don't
# block publish either.
#
# name is required regardless of registry_status - 9.01 item 1 wants a
# sponsor name on the certificate no matter who the sponsor is.
# national_registry_id is required only once the sponsor claims to be
# registered (feature 027): requiring it unconditionally compelled an
# unregistered sponsor to invent a registry ID just to publish, which is a
# worse outcome than the missing field the rule was written to prevent - see
# current-feature.md.
FIELD_LABELS = {
    "name": "sponsor name",
    "national_registry_id": "NASBA sponsor registry ID",
}


def get_sponsor_profile(db: Session) -> SponsorProfile:
    # Always present - the migration that created this table seeded row id
    # 1, and the singleton CHECK means nothing can ever delete or duplicate
    # it through this application.
    return db.get(SponsorProfile, 1)


def required_fields(profile: SponsorProfile) -> list[str]:
    fields = ["name"]
    if profile.registry_status == REGISTRY_STATUS_REGISTERED:
        fields.append("national_registry_id")
    return fields


def missing_fields(profile: SponsorProfile) -> list[str]:
    return [FIELD_LABELS[field] for field in required_fields(profile) if not getattr(profile, field).strip()]


def update_sponsor_profile(db: Session, updates: dict) -> SponsorProfile:
    profile = get_sponsor_profile(db)
    for field, value in updates.items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile
