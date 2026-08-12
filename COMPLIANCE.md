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

## Standards Compliance Mapping

Quoted from `docs/2026-Statement-on-Standards-for-CPE-Programs.pdf`
(August 2026 edition, effective 2026-08-01). Cross-referenced against
`docs/2024-to-2026-Standards-Crosswalk.pdf` where relevant.

### Feature 020 — Program metadata and learning objectives

| Locator | Requirement | Feature | Where in code | Gap |
| --- | --- | --- | --- | --- |
| 3.01 | "Sponsored learning activities must be based on relevant learning objectives and outcomes assigned to the learning activities that clearly articulate the professional competence that should be achieved by participants in the learning activities. When determining the learning objectives, program sponsors must consider the program knowledge level and prerequisite education/experience for the learning activity." | 020 | `app/models/learning_objective.py`; `validate_for_publish` in `app/services/admin_content.py` requires at least one non-blank objective before publish | |
| 3.01.1 | "Learning activities provided by CPE program sponsors must specify the knowledge level, content, and learning objectives so that potential participants can determine whether the learning outcomes are appropriate to their professional competence development needs, except as provided in Section 8 Paragraph 8.01 for mandatory internal courses. Knowledge levels consist of Basic, Intermediate, Advanced, Update, and Overview." | 020 | `Course.program_level` (`app/models/course.py`, CHECK constraint in migration `9dd63108687a`), `app/constants/program_levels.py`; disclosed via `GET /courses/{slug}` and `CourseDetail.jsx` | abacadaba has no mandatory-internal-course concept, so the 8.01 exception is not modeled |
| 3.02.1 | "To the extent it is possible to do so, CPE program sponsors should make every attempt to equate program content and knowledge level with the backgrounds of intended participants. All programs identified as Intermediate, Advanced or Update must clearly identify prerequisite education, experience, and advance preparation in precise language so that potential participants can readily ascertain whether they qualify for the program. For courses with a program knowledge level of Basic and Overview, prerequisite education or experience and advance preparation, should be noted if applicable, otherwise, state \"none\" in the course announcement or descriptive materials." | 020 | `validate_for_publish` in `app/services/admin_content.py` (rule 4/5); `Course.prerequisites`/`Course.advance_preparation`; `CourseDetail.jsx` renders literal "None" rather than omitting the row | Text is free-form, not validated for "precise language" — that's editorial judgment, not something a constraint can check |
| 8.01.1 | "For potential participants to effectively plan their CPE, the program sponsor must disclose the significant features of the program in advance (for example, through the use of brochures, websites, electronic notices, invitations, direct mail, or other announcements). When CPE programs are offered in conjunction with non-educational activities or when several CPE programs are offered concurrently, participants must receive an appropriate schedule of events indicating those components that are recommended for CPE credit. The CPE program sponsor's registration and attendance policies and procedures must be formalized, published, and made available to participants and include refund and cancellation policies as well as complaint resolution policies." | 020 | `GET /courses/{slug}` (`app/routers/courses.py`, `app/schemas/course.py`); `CourseDetail.jsx` shows objectives, level, field of study, prerequisites, and advance preparation before enrollment | Refund, cancellation, and complaint resolution policies are not published anywhere yet — those are site-wide static pages, not course fields (feature 026) |
| 8.01.2 | "CPE program sponsors must distribute program materials in a timely manner and encourage participants to complete any advance preparation requirements. All programs must clearly identify prerequisite education, experience, and advance preparation requirements, if any, in the descriptive materials. Prerequisites, if any, must be written in precise language so that potential participants can readily ascertain whether they qualify for the program." | 020 | Same as 3.02.1: `Course.prerequisites`/`Course.advance_preparation`, disclosed via `GET /courses/{slug}` and rendered in `CourseDetail.jsx` | |
