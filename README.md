# abacadaba

Micro-learning. A user watches a ~5 minute video, takes a 5-question multiple
choice quiz, gets a small burst of confetti for each correct answer, and at 4/5
or better passes: bigger confetti plus a downloadable certificate.

## Stack
- Backend: Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Postgres 16
- Frontend: React 18 + Vite, plain JavaScript, CSS Modules
- Video storage: DigitalOcean Spaces (S3-compatible) via boto3, presigned URLs

## Getting started
    docker compose up -d
    cd backend && source .venv/bin/activate && uvicorn app.main:app --reload
    cd frontend && npm run dev
    cd backend && pytest
