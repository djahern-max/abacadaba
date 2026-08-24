from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_admin
from app.schemas.sponsor_profile import AdminSponsorProfile, AdminSponsorProfileUpdate
from app.services import sponsor_profile as sponsor_profile_service

router = APIRouter(dependencies=[Depends(require_admin)])


def _to_schema(profile) -> AdminSponsorProfile:
    return AdminSponsorProfile(
        name=profile.name,
        national_registry_id=profile.national_registry_id,
        state_registry_ids=profile.state_registry_ids,
        website=profile.website,
        contact_email=profile.contact_email,
        address=profile.address,
        registry_status=profile.registry_status,
        updated_at=profile.updated_at,
        missing_fields=sponsor_profile_service.missing_fields(profile),
    )


@router.get("/admin/sponsor", response_model=AdminSponsorProfile)
def get_sponsor(db: Session = Depends(get_db)):
    return _to_schema(sponsor_profile_service.get_sponsor_profile(db))


@router.patch("/admin/sponsor", response_model=AdminSponsorProfile)
def update_sponsor(payload: AdminSponsorProfileUpdate, db: Session = Depends(get_db)):
    profile = sponsor_profile_service.update_sponsor_profile(db, payload.model_dump(exclude_unset=True))
    return _to_schema(profile)
