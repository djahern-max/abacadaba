from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware.viewer import ViewerIdentityMiddleware
from app.routers import admin, attempts, auth, certificates, health, lessons, quiz, watch

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
app.include_router(lessons.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(quiz.router, prefix="/api/v1")
app.include_router(attempts.router, prefix="/api/v1")
app.include_router(certificates.router, prefix="/api/v1")
app.include_router(watch.router, prefix="/api/v1")
