import pytest
from sqlalchemy import update

from app.db import SessionLocal
from app.models.sponsor_profile import SponsorProfile

# sponsor_profile is a real singleton row (id 1, CHECK-enforced), not scoped
# to a single test the way a course fixture is - so every test gets one
# reset here rather than each publish-flow test wiring its own. Individual
# tests that care about an incomplete profile (app/services/sponsor_profile
# .py's publish gate, or the sponsor settings endpoints themselves) mutate
# it further within their own body, after this has already run.
DEFAULT_SPONSOR = {
    "name": "Test Sponsor, Inc.",
    "national_registry_id": "123456",
    "state_registry_ids": None,
    "website": "https://sponsor.example.com",
    "contact_email": "sponsor@example.com",
    "address": "1 Test Way, Example, ST 00000",
}


@pytest.fixture(autouse=True)
def reset_sponsor_profile():
    db = SessionLocal()
    db.execute(update(SponsorProfile).where(SponsorProfile.id == 1).values(**DEFAULT_SPONSOR))
    db.commit()
    db.close()
    yield
