# Changelog

Completed features, oldest first. Append only.

## 2026-08-04, Feature 001, Walking skeleton
Backend (FastAPI + SQLAlchemy + Alembic) and frontend (React + Vite) now talk to
Postgres end to end: GET /api/v1/health checks the database and the app shows a
green/red connection status pill. Vite boilerplate removed, global CSS variables added.
