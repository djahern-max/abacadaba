from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware.viewer import ViewerIdentityMiddleware
from app.routers import (
    admin,
    admin_analytics,
    admin_completions,
    admin_currency,
    admin_sponsor,
    attempts,
    auth,
    certificates,
    courses,
    evaluations,
    health,
    meta,
    og,
    policies,
    review,
)

docs_enabled = settings.environment != "production"
app = FastAPI(
    title="abacadaba API",
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ViewerIdentityMiddleware)

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(courses.router, prefix="/api/v1")
app.include_router(meta.router, prefix="/api/v1")
app.include_router(policies.router, prefix="/api/v1")
app.include_router(og.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(admin_analytics.router, prefix="/api/v1")
app.include_router(admin_sponsor.router, prefix="/api/v1")
app.include_router(admin_completions.router, prefix="/api/v1")
app.include_router(admin_currency.router, prefix="/api/v1")
app.include_router(attempts.router, prefix="/api/v1")
app.include_router(certificates.router, prefix="/api/v1")
app.include_router(review.router, prefix="/api/v1")
app.include_router(evaluations.router, prefix="/api/v1")
