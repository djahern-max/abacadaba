# Changelog

Completed features, oldest first. Append only.

## 2026-08-04, Feature 001, Walking skeleton
Backend (FastAPI + SQLAlchemy + Alembic) and frontend (React + Vite) now talk to
Postgres end to end: GET /api/v1/health checks the database and the app shows a
green/red connection status pill. Vite boilerplate removed, global CSS variables added.

## 2026-08-04, Feature 002, Lessons: model, API, and browsing
Lessons are a real domain object now: a Postgres-backed lessons table, list and
detail endpoints under /api/v1, an idempotent seed script with three sample
lessons, and client-side routing with a lesson grid and a detail page with a
16:9 "video coming soon" placeholder.

## 2026-08-04, Feature 003, Video storage and playback
Lessons can now have a video in a private DigitalOcean Space. Added a Spaces
storage service (presigned GET URLs, private uploads), a video-url endpoint,
a shared-secret-guarded admin upload endpoint, and an upload_video CLI. The
lesson detail page plays the video inline via a VideoPlayer component with a
reload button for expired presigned URLs, falling back to the existing
placeholder when no video has been uploaded yet.
