from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_admin
from app.schemas.policy import PolicyPublic, PolicyUpdate
from app.services import policies as policies_service

router = APIRouter()


def _to_schema(policy) -> PolicyPublic:
    return PolicyPublic(
        slug=policy.slug,
        title=policy.title,
        body=policy.body,
        updated_at=policy.updated_at,
        is_placeholder=policies_service.is_placeholder(policy),
    )


@router.get("/policies", response_model=list[PolicyPublic])
def list_policies(db: Session = Depends(get_db)):
    return [_to_schema(policy) for policy in policies_service.list_policies(db)]


@router.get("/policies/{slug}", response_model=PolicyPublic)
def get_policy(slug: str, db: Session = Depends(get_db)):
    try:
        policy = policies_service.get_policy(db, slug)
    except policies_service.PolicyNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Policy not found") from exc
    return _to_schema(policy)


@router.patch("/admin/policies/{slug}", response_model=PolicyPublic, dependencies=[Depends(require_admin)])
def update_policy(slug: str, payload: PolicyUpdate, db: Session = Depends(get_db)):
    try:
        policy = policies_service.update_policy(db, slug, payload.model_dump(exclude_unset=True))
    except policies_service.PolicyNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Policy not found") from exc
    return _to_schema(policy)
