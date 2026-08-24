from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_admin
from app.schemas.currency import CurrencyDashboardOut
from app.services import currency as currency_service

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/admin/currency", response_model=CurrencyDashboardOut)
def get_currency_dashboard(db: Session = Depends(get_db)):
    return currency_service.get_dashboard(db)
