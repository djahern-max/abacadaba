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

## 2026-08-04, Feature 008, Accounts, real auth, and progress
Real accounts arrive: users and sessions tables (opaque bcrypt-backed
sessions, 30-day httpOnly/SameSite=Lax cookies, no JWT), a user_id on
attempts (nullable, ON DELETE SET NULL, anonymous quizzes still work),
and /auth/register, /auth/login, /auth/logout, and /auth/me. The
shared-secret upload guard from feature 003 is gone, replaced by a
real is_admin check (require_admin: 401 signed out, 403 non-admin) and
a make_admin CLI to promote the first account; upload_video.py now
logs in instead of sending a header. Certificates claimed by a signed
in user use the account's display_name automatically instead of a
typed name, and the verify page and CertificateVerification say so.
GET /me/attempts feeds a new /me progress page. On the frontend, an
AuthContext wraps the app, the header shows sign in/out state, Login
and Register pages handle the forms, and the result page skips the
name form entirely and auto-claims when signed in, replacing the
feature 007 localStorage persistence with the certificate_code the
API now returns on the attempt result itself.

## 2026-08-06, Feature 009, Deploy to production
abacadaba.com is live on the public internet. Re-specced mid-flight from
DigitalOcean App Platform to a Droplet (Ubuntu 24.04, Docker Compose, nginx,
Postgres in a container) for cost and to keep building raw-VM ops skills; the
container image is unchanged so the original target stays a drop-in option.
The API lives on api.abacadaba.com and the frontend on abacadaba.com,
sharing a registrable domain so SESSION_COOKIE_DOMAIN=.abacadaba.com works
with SameSite=Lax rather than needing SameSite=None. The Droplet never runs
npm or installs Node — the frontend is built off-box and only dist/ is
shipped — closing off the postinstall-script compromise vector that hit an
earlier project. Backend changes: a non-root Dockerfile, config-driven
cookie/CORS/docs settings (docs disabled in production), a DATABASE_URL
scheme normalizer for psycopg, and a DB-backed /api/v1/health. Host
hardening: key-only SSH restricted to the deploy user, ufw plus a matching
DigitalOcean Cloud Firewall, and docker-compose.prod.yml running the db on
an internal-only network with no published ports and the api bound to
127.0.0.1 with dropped capabilities and a read-only filesystem. deploy.sh
encodes the required order — migrate, then restart the api — so a failed
migration halts the deploy instead of leaving the api on a mismatched
schema. DEPLOYMENT.md and HARDENING.md document the layout, env vars, and
the reasoning behind each control. Monitoring/alerting and automated
backups are feature 013; CDN/transcoding and staging/blue-green deploys
remain out of scope.

## 2026-08-06, Feature 010, Admin authoring
An admin can now create a lesson, upload its video, write its five
questions, and publish it entirely in the browser, no CLI or seed
script required. Backend: AdminLesson/AdminQuestion/AdminChoice
schemas (deliberately kept separate from the leak-free public ones,
which stay is_correct-free), an admin_content service with full
lesson/question/choice CRUD, move-up/move-down reordering that
renumbers the whole set in two passes to dodge the position unique
constraint, set_correct_choice clearing every other choice on the
same question in one transaction, and validate_for_publish returning
every failed rule at once (exactly 5 questions, video uploaded,
title/slug/description non-empty, each question 2+ choices with
exactly one correct). All /admin/* routes sit behind require_admin at
the router level. Deleting a lesson with completed attempts is
refused with a 409 rather than orphaning attempt data. scripts/seed.py
is retired to a bootstrap-only role now that the admin UI is the real
authoring path. Frontend: a new /admin section (lesson list with
published state/question count/video presence, and a per-lesson
editor with details, video upload with a progress bar, and inline
question/choice editing with move and correct-choice controls),
gated by an AdminGuard that redirects signed-out visitors to login
and shows a plain not-authorized message to signed-in non-admins: the
Admin link itself never renders for a non-admin. The publish button
shows the server's validation checklist and disables itself until the
next edit, since the same checklist would just repeat on retry.
Measured time to author one complete lesson by hand, from an empty
form to published: about 5 minutes.

## 2026-08-06, Feature 011, Watch tracking and quiz gating
The quiz now unlocks only after someone has actually watched enough of
the video; seeking to the end no longer counts. Every request gets a
viewer_id (a new ViewerIdentityMiddleware sets a one-year httpOnly
cookie for anonymous visitors, read via a get_viewer_id dependency
everywhere else), and a watch_progress table (unique on lesson_id +
viewer_id, optionally carrying user_id) tracks watched_seconds against
a new required_watch_ratio on lessons (default 90%, admin-editable as
a percentage). The player sends a heartbeat roughly every 10 seconds;
app/services/watch.py credits time only when the gap since the last
heartbeat is at least 8 seconds, the position has advanced by no more
than 15 seconds, and the position is within the lesson's duration —
credit is the smaller of the position delta and the wall-clock delta.
A backward jump (a rewind) resets the comparison point without
crediting anything, and POSTs faster than about one every 5 seconds
get a 429 rather than silently no-opping, both proven out with a
FLOOD and a SKIP test. A signed-in user's progress is looked up by
viewer_id OR user_id, so it follows them to a new device once they're
signed in on it. POST /lessons/{slug}/attempts now 403s with how much
video remains when the gate isn't met, checked via the same
is_unlocked function the frontend reads from; admins bypass it
entirely so authoring can be tested without watching. The quiz
delivery endpoint (GET .../quiz) was deliberately left open rather
than gated too — nothing sensitive lives there since it already omits
is_correct, and gating it as well would only complicate the "preview
the questions" case for no real security benefit. On the frontend,
VideoPlayer throttles heartbeats to actual playback (stopped on
pause, flushed on ended and on tab-hide via visibilitychange) and
renders a plain-text progress bar; LessonDetail's "Take the quiz"
button reads that same progress live and swaps from a disabled
explanation to the real link the moment the threshold is crossed, no
refresh needed. Reaching the quiz URL directly while still gated shows
the server's own explanation with a link back to the lesson instead of
a bare 403. A lesson with no duration_seconds can't gate by
definition, so it's simply ungated, with a warning surfaced in the
admin editor when duration is missing. Feature 012's per-second
heatmaps and resuming playback where you left off remain out of
scope; so does retroactively applying the gate to attempts completed
before this feature shipped.
