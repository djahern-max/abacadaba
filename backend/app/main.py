from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import admin, attempts, certificates, health, lessons, quiz

app = FastAPI(title="abacadaba API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(lessons.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(quiz.router, prefix="/api/v1")
app.include_router(attempts.router, prefix="/api/v1")
app.include_router(certificates.router, prefix="/api/v1")
