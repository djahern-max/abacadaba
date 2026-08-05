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

## 2026-08-04, Feature 004, Quiz data model and delivery
Lessons now have real quiz content: questions and choices tables (cascading,
position-ordered), a GET /lessons/{slug}/quiz endpoint served through
schemas that never include is_correct, and a seeded five-question quiz for
each of the three lessons. The frontend has a read-only quiz page listing
every question with lettered choices, reachable via a "Take the quiz" button
on the lesson detail page. Answering, grading, and scoring are feature 005.

## 2026-08-04, Feature 005, Taking the quiz with per answer confetti
Added POST /lessons/{slug}/quiz/answers to grade one answer at a time
(400 on a choice from a different question, 404 on an unknown or
cross-lesson question). The quiz page now walks through one question at a
time with a progress bar: pick a choice, Submit grades it, a correct
answer fires a small canvas-confetti burst (skipped under
prefers-reduced-motion), a wrong answer reveals the correct choice in
green, and Next/Finish advances to a "Quiz complete" placeholder. Choices
are real buttons with visible focus rings and an aria-live announcement
of the result. Scoring, pass/fail, and the attempts table are feature 006.

## 2026-08-04, Feature 006, Attempts, scoring, and passing at 4 of 5
Added attempts and attempt_answers tables (the latter unique on
attempt_id + question_id, the DB-level replay guard) plus
POST /lessons/{slug}/attempts, POST /attempts/{id}/answers, and
GET /attempts/{id}/result, replacing and removing the sessionless
POST /lessons/{slug}/quiz/answers from feature 005. The server now owns
scoring and pass/fail (PASS_THRESHOLD = 4) and rejects a question
answered twice in the same attempt with a 409. The quiz page starts an
attempt on load and redirects to /attempts/:attemptId on the final
answer; the new results page shows the score and pass/fail state,
fires a bigger, staggered confetti burst on a pass, and offers rewatch
and retry links on a fail. Certificates land in feature 007.

## 2026-08-04, Feature 007, Certificate generation and download
Passed attempts can now earn a downloadable PDF certificate. Added
recipient_name and certificate_code (confusion-free, hyphenated,
unique) columns to attempts, POST /attempts/{id}/certificate to claim
one (409 if not passed/complete), GET /attempts/{id}/certificate.pdf
to stream a reportlab-rendered landscape PDF (font shrinks to fit long
names or titles), and GET /certificates/{code} for case- and
hyphen-insensitive public verification, returning valid: false rather
than a 404 for unknown codes. The results page now offers a name entry
form on a pass that reveals the code and a plain download link once
claimed (persisted in localStorage so a reload skips the form), and a
new /verify/:code page renders the certificate details or a clear
not-found state, wording things as self-reported since there are no
accounts yet. SITE_URL/VITE_SITE_URL back the verification URL printed
on the certificate. Feature 008 will replace the typed name with an
authenticated user.
