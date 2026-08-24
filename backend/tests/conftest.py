import pytest
from sqlalchemy import update

from app.constants.policies import SEEDED_POLICIES
from app.db import SessionLocal
from app.models.policy import Policy
from app.models.sponsor_profile import SponsorProfile

# sponsor_profile is a real singleton row (id 1, CHECK-enforced), not scoped
# to a single test the way a course fixture is - so every test gets one
# reset here rather than each publish-flow test wiring its own. Individual
# tests that care about an incomplete profile (app/services/sponsor_profile
# .py's publish gate, or the sponsor settings endpoints themselves) mutate
# it further within their own body, after this has already run.
# registry_status defaults to "registered" here, not the model's own
# "not_registered" default (app/models/sponsor_profile.py) - every
# feature-024 certificate test written before this feature shipped asserts
# the NASBA time statement and a registry ID are present on the PDF/verify
# payload, and none of them know this field exists. Defaulting the shared
# fixture to "registered" keeps that whole suite proving 024's original
# behaviour unchanged, exactly what this feature's acceptance criteria
# require ("flipping to registered restores 024's certificate exactly").
# Feature 027's own tests (tests/test_certificates.py,
# tests/test_sponsor_profile.py) flip individual attempts to
# "not_registered" within their own body.
DEFAULT_SPONSOR = {
    "name": "Test Sponsor, Inc.",
    "national_registry_id": "123456",
    "state_registry_ids": None,
    "website": "https://sponsor.example.com",
    "contact_email": "sponsor@example.com",
    "address": "1 Test Way, Example, ST 00000",
    "registry_status": "registered",
}


@pytest.fixture(autouse=True)
def reset_sponsor_profile():
    db = SessionLocal()
    db.execute(update(SponsorProfile).where(SponsorProfile.id == 1).values(**DEFAULT_SPONSOR))
    db.commit()
    db.close()
    yield


# Feature 026: publish refuses while any of the four seeded policies is still
# placeholder text. Same reasoning as reset_sponsor_profile above - a global
# gate, not scoped to one test's course fixture, so every test gets real
# (non-placeholder) policy text here rather than each publish-flow test
# writing its own. Tests that care about the placeholder state itself
# (tests/test_policies.py, the publish-refusal test in
# tests/test_admin_content.py) overwrite a policy back to placeholder text
# within their own body, after this has already run.
@pytest.fixture(autouse=True)
def reset_policies():
    db = SessionLocal()
    # Reset title too, not just body - a test that PATCHes a policy's title
    # (tests/test_policies.py) would otherwise leave it changed for every
    # later test in the same run, including ones that assert on the seeded
    # title text in a publish-refusal message.
    for slug, title in SEEDED_POLICIES:
        db.execute(
            update(Policy).where(Policy.slug == slug).values(title=title, body="Real policy text for tests.")
        )
    db.commit()
    db.close()
    yield
