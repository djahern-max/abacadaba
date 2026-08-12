# abacadaba.com

## Overview

**abacadaba.com** is a micro-learning platform.

A user:

1. Watches a ~5-minute video.
2. Takes a 5-question multiple-choice quiz.
3. Gets a small burst of confetti for each correct answer.
4. Passes with a score of **4/5 or better**.
5. On passing, gets bigger confetti plus a downloadable certificate.

The name is a play on guessing your way through a multiple-choice test.

## Stack

### Backend
- Python 3.12
- FastAPI
- SQLAlchemy 2.0
- Alembic
- Postgres 16

### Frontend
- React 18
- Vite
- Plain JavaScript — no TypeScript
- CSS Modules

### Video Storage
- DigitalOcean Spaces
- S3-compatible via `boto3`
- Presigned URLs

### Local Development
- Postgres runs in Docker

## Project Layout

```text
backend/            FastAPI app (see backend/CLAUDE.md)
frontend/           Vite React app (see frontend/CLAUDE.md)
current-feature.md  the ONE feature being built right now
CHANGELOG.md        completed features, append only
```

## Workflow — Read This First

`current-feature.md` is the single source of truth. Build exactly what it describes.

Do not build anything outside the feature's scope. If you hit something needed but out of scope, finish the feature and list it at the end of your response.

When every acceptance criterion passes:

1. Append a short entry to `CHANGELOG.md`.
2. Include the date and feature number.
3. Add one or two lines describing what shipped.
4. Say the feature is done.

Never rewrite `CHANGELOG.md` history. Append only.

## Conventions

- Use `snake_case` in Python and in the database.
- Use `camelCase` in JavaScript.
- Use `PascalCase` for components.
- API routes live under `/api/v1`.
- Every model change ships with its Alembic migration in the same change.
- Secrets go in `.env` and are never committed.
- Add new environment variables to `.env.example` as well.
- Prefer small, readable code over clever code.
- Justify any new dependency.

## Commands

### Start Docker Services

```bash
docker compose up -d
```

### Run Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

### Run Frontend

```bash
cd frontend
npm run dev
```

### Run Backend Tests

```bash
cd backend
pytest
```
