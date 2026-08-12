# abacadaba.com

Micro-learning with a compliance spine. A user works through short video
segments and answers multiple choice questions to earn a certificate.
The name is a play on guessing your way through a multiple choice test.

Currently a lesson is the unit and passing is 4/5, but the app is being rebuilt
around the NASBA 2026 CPE Standards: courses become the credit-bearing unit,
question counts derive from computed credit, and pass thresholds are per-course.
Where this file and current-feature.md disagree, the feature wins.

abacadaba is deliberately non-financial. It is the rehearsal for superCPE, which
will offer NASBA-registered CPE to CPAs. The compliance machinery here is meant
to be identical; only the subject matter differs.

## Stack
- Backend: Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Postgres 16
- Frontend: React 18 + Vite, plain JavaScript (no TypeScript), CSS Modules
- Video storage: DigitalOcean Spaces (S3-compatible) via boto3, presigned URLs
- Local Postgres runs in Docker

## Layout
    backend/            FastAPI app (see backend/CLAUDE.md)
    frontend/           Vite React app (see frontend/CLAUDE.md)
    docs/               2026 CPE Standards, Fields of Study, 2024-to-2026 crosswalk
    current-feature.md  the ONE feature being built right now
    CHANGELOG.md        completed features, append only
    COMPLIANCE.md       Standards locator mapping, append only

## Workflow, read this first
1. current-feature.md is the single source of truth. Build exactly what it describes.
2. Do not build anything outside the feature's scope. If you hit something needed
   but out of scope, finish the feature and list it at the end of your response.
3. When every acceptance criterion passes, append a short entry to CHANGELOG.md
   (date, feature number, one or two lines on what shipped), append any Standards
   mapping to COMPLIANCE.md (see below), and say the feature is done.
4. Never rewrite CHANGELOG.md or COMPLIANCE.md history. Append only.

## Conventions
- snake_case in Python and in the database, camelCase in JS, PascalCase for components.
- API routes live under /api/v1.
- Every model change ships with its Alembic migration in the same change.
- Secrets go in .env, never committed. Add new vars to .env.example too.
- Prefer small readable code over clever code. Justify any new dependency.

## Commands
    docker compose up -d
    cd backend && source .venv/bin/activate && uvicorn app.main:app --reload
    cd frontend && npm run dev
    cd backend && pytest

## COMPLIANCE.md

Features 019 and later are CPE compliance work by default. Append to
COMPLIANCE.md unless the feature genuinely maps to no locator, and say so
explicitly in your summary when you conclude that.

One row per Standards locator the feature satisfies. Cite locators only from
docs/2026-Statement-on-Standards-for-CPE-Programs.pdf, which is in this repo —
quote the locator's own words in the Requirement column rather than
paraphrasing from memory. If you cannot find the locator in that PDF, write
UNVERIFIED in the Locator column and say so in your summary. Do not guess a
locator number.

Where a feature only partially satisfies a locator, say what is still missing in
the Gap column rather than marking it done. A row with an empty Gap column is a
claim that nothing is outstanding for that locator.

Row format:

    | Locator | Requirement | Feature | Where in code | Gap |

The Standards in docs/ are the August 2026 edition, effective 2026-08-01. Earlier
editions renumbered their locators, so a locator cited in outside material may
not match; docs/2024-to-2026-Standards-Crosswalk.pdf maps between them.
