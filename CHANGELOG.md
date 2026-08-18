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

## 2026-08-06, Feature 012, Question analytics and retake policy
An admin can now see which questions people get wrong and where they
drop off, and retaking a quiz no longer replays the same five
questions in the same order. Added shuffle_seed to attempts (a random
int generated on attempt creation) plus retake_cooldown_minutes and
max_attempts to lessons; also added viewer_id to attempts (not called
out in the original data-model note, but required to count anonymous
retakes by the feature 011 cookie the same way signed-in ones are
counted by user_id). app/services/quiz.py derives question and choice
order deterministically from the seed (a folded seed+salt int, since
random.Random only accepts a single scalar) — GET .../quiz now takes
an optional attempt_id and serves shuffled order for it, authored
order without it; the leak test still passes since ChoicePublic is
built the same way either way. app/services/attempts.py enforces the
retake policy in start_attempt before creating a row: max_attempts
compares completed-attempt counts, the cooldown compares against the
most recent completed_at, both keyed by user_id when signed in and by
viewer_id otherwise (a cleared cookie resets an anonymous viewer's
count — noted in the code as accepted for now), and admins bypass
both, both returning 429. app/services/analytics.py is four read-only
aggregate queries (lesson_stats, question_stats, choice_distribution,
dropoff) straight from attempt_answers, no new reporting tables,
exposed as GET /admin/lessons/{id}/stats behind require_admin.
Frontend: a new /admin/lessons/:id/stats page (linked from the lesson
list and editor) with a summary row, a worst-first question table
flagging anything under 40% correct, expandable per-question choice
distributions, and a drop-off list, showing a plain message instead
of an empty table when a lesson has no attempts yet; the Quiz page
now starts the attempt before fetching the quiz so it can pass
attempt_id along, and reads a 429's detail message on both the locked
(watch gate) and limited (retake policy) paths; the lesson editor's
Details form exposes retake cooldown and max attempts with helper
text explaining that blank means unlimited. Question banks larger
than five with random selection, per-user analytics and exports, and
charts beyond a plain table remain out of scope.

## 2026-08-07, Feature 013, Sign in with Google
A visitor can now sign in or register with a Google account and land in the
exact same session mechanism as a password account: Google only replaces the
identity check, then the existing create_session/_set_session_cookie takes
over untouched. Added google_sub (unique, nullable) to users and made
password_hash nullable for Google-only accounts, plus three optional
GOOGLE_CLIENT_ID/SECRET/REDIRECT_URI settings that make /auth/google/start
404 (and the frontend button disappear via the same failure mode) when
unset, so a half-configured deploy fails visibly. app/services/google_auth.py
keeps every authlib and HTTP call contained to that one module: it builds
the authorization URL, exchanges the code and verifies the ID token's
signature against Google's JWKS, and resolves identity in the required
order — match google_sub, else match a verified email and link, else create
a new user with password_hash NULL. An unverified email on an existing
address is refused rather than linked, which is the account-takeover trap
this feature is built around. GET /auth/google/start and
/auth/google/callback are the only new routes, both redirects rather than
JSON since the browser arrives from Google, not apiFetch; state is a random
token round-tripped through a short-lived httpOnly cookie, and any failure
(state mismatch, bad code, unverified email) redirects to
/login?error=<code> instead of a bare 400. Fixed a latent bug this feature
would otherwise have exposed: auth_service.authenticate() called
verify_password(password, user.password_hash) unconditionally, which would
have thrown on a Google-only account's None hash; it now falls through to
the same dummy-hash comparison as a missing user, so a password attempt
against a Google-only account is a uniform-timing 401, not a 500 or an
oracle for which addresses are Google-only. On the frontend, a new
GoogleButton component (full page redirect to /auth/google/start, not
apiFetch) sits above the existing form on both Login and Register with a
Google-brand-styled button and an "or" divider; AuthContext's existing
getMe()-on-mount needed no changes to pick up the session after the
callback redirects back. Apple/GitHub/Microsoft sign-in, unlinking Google,
adding a password to a Google-only account, and refresh tokens/storing
Google access tokens remain out of scope; the last two need a password
reset flow that doesn't exist yet.

## 2026-08-07, Feature 014, Header cleanup and password field polish
The feature 001 backend status pill is gone from the header (and its
App.jsx health-check polling and src/api/health.js with it), leaving just
the wordmark and auth nav; GET /api/v1/health itself is untouched. A new
shared PasswordInput component (inline SVG eye toggle, per-field
visibility state, type="button" to avoid submitting the form it sits in)
replaces the bare password inputs on Login and Register, and Register
gained a Confirm password field validated on submit — after name length
and password length — with "Passwords do not match." reusing the
existing validate() rather than a second path. Password reset, strength
meters, and a frontend test framework remain out of scope.

## 2026-08-11, Feature 015, Watch progress correctness
Closed the leak where two people signing into the same browser inherited
each other's watch history: app/services/watch.py resolved progress by
`viewer_id OR user_id`, so a signed-out user's cookie still matched the
next person's row. Progress is now resolved by identity, not union —
signed in matches `user_id` alone, anonymous matches `viewer_id` alone
among unclaimed (`user_id IS NULL`) rows — in one function,
`_identity_filter`. Migration 6f58cd9b86ef swaps the old
`(lesson_id, viewer_id)` unique constraint for two partial unique
indexes, one per identity, after collapsing any pre-existing duplicate
rows by `user_id`; `downgrade -1` restores the original constraint.
`viewer_id` now rotates on sign out (defence in depth), and
`claim_anonymous_progress()` folds a browser's anonymous progress into
the account at sign in — register, login, and the Google callback all
call it before responding, taking the larger `watched_seconds` when the
user already has their own row so a returning viewer never loses
progress. On the frontend, the watch readout now measures against the
lesson's full duration instead of the unlock threshold (no more "5:09 of
4:41"), swapping to a plain "Watched" state once unlocked; the progress
bar is driven by the video's own `timeupdate` event for smooth movement,
reconciled to the server's value on every heartbeat response, while the
heartbeat POST cadence itself is unchanged. Requiring sign-in to take a
quiz and resuming playback where a viewer left off remain out of scope.

## 2026-08-11, Feature 016, Require sign in to take a quiz

`POST /lessons/{slug}/attempts` now requires a signed-in user — a
signed-out request gets 401 before the watch gate or retake policy are
even checked, so a visitor is told to sign in rather than how much
video is left. The retake-policy keying dropped its `viewer_id`
fallback since every new attempt now has a `user_id`; `attempts.user_id`
itself stays nullable and every downstream endpoint (answering, reading
a result, claiming a certificate) is still unguarded, so historical
anonymous attempts and their certificates keep working exactly as
before. On the frontend, `LessonDetail` swaps the quiz button for a
"Sign in to take the quiz" link (to `/login`, carrying `state.from` back
to the lesson) whenever there's no signed-in user, and renders a neutral
state while `AuthContext` is still resolving so a signed-in visitor
never sees the prompt flash. `Quiz` redirects straight to `/login` with
the same `from` state if reached directly while signed out, instead of
rendering an error. The anonymous name-entry form on `Result` is
unreachable for new attempts but stays in place for old certificate
links.

## 2026-08-11, Feature 017, Authoring UX
Authoring a lesson stops tripping the author over gaps between what the
form shows and what the server actually requires. Backend: `POST
/admin/lessons/{id}/publish` gained a `dry_run` query flag that runs the
same `validate_for_publish` and returns `{"errors": [...]}` without
touching `is_published`, so the frontend has a side-effect-free way to
read the same rules instead of a second copy of them. On the frontend,
`VideoUploader` reads `video.duration` off an offscreen `<video>` element
on file selection (object URL created and revoked, value rounded down)
and hands it up to `DetailsForm`, which fills the still-editable duration
field and marks it as auto-filled until the author types over it.
`DetailsForm` also lifts its existing dirty check up to
`AdminLessonEditor`, which now disables Publish with "Save your details
first." while dirty, and warns via `beforeunload` (plus a confirm on the
in-app "All lessons" link) whenever details are unsaved or a video
upload is running — uploading no longer blocks editing questions or
details, replaced a blocking progress bar with an "Uploading… N%" /
"Processing…" status line, and says plainly that leaving cancels it. A
new shared `FileInput` component (visually-hidden input behind a real
`<label for>`, focus-visible on the styled button, selected filename
shown beside it) replaces the bare `<input type="file">`. `PublishPanel`
now renders a permanent six-item checklist (title, slug, description,
video, five questions, one correct choice each) driven entirely by the
dry-run error list, ticking items off as edits are saved rather than
only speaking up after a failed publish click. Queued/background
uploads, transcoding, and thumbnails (feature 018) remain out of scope.

## 2026-08-11, Feature 018, Lesson thumbnails
A lesson now carries a `thumbnail_key` (nullable, added via migration
`af95594e5536`), mirroring `video_key`: private object in Spaces, served
through a presigned GET, `lessons/<slug>-thumb.<ext>` since the
extension varies with upload. `POST /admin/lessons/{id}/thumbnail`
validates the declared content type, caps the file at 2 MB, then opens
the bytes with Pillow (added as a direct dependency; it was already
pulled in transitively by reportlab) to confirm they actually decode as
the claimed JPEG/PNG/WebP — the declared content type alone is a
browser guess off the filename, so a PDF renamed to `.jpg` would
otherwise sail through. A non-16:9 upload is accepted with a `warning`
in the response rather than rejected. Replacing a thumbnail overwrites
the old object (`storage.delete_object`, new) when the extension
changes rather than leaving it behind. `GET /lessons/{slug}/thumbnail-url`
mirrors `video-url` (404 when unset, 3600s expiry); `LessonSummary`
gained a `has_thumbnail` bool (a `Lesson.has_thumbnail` property) so the
list page knows whether to fetch a URL without a presign per card.
Frontend: `LessonCard` reserves a 16:9 box via `aspect-ratio` (plain
placeholder when there's no thumbnail, so the grid never reflows) with
`alt` set to the lesson title since the card is a link; `VideoPlayer`
sets `poster` from the same endpoint, fixing the black rectangle before
playback. `AdminLessonEditor` gained a `ThumbnailUploader` beside
`VideoUploader`, reusing `FileInput` from feature 017; it previews the
just-picked file immediately via `URL.createObjectURL` (so upload and
replace both show without a hard refresh, independent of publish
state) and surfaces the aspect-ratio warning inline. Thumbnail
generation from a video frame, multiple sizes/`srcset`, and a CDN
remain out of scope.

## 2026-08-12, Feature 019, Courses as the credit-bearing unit
The unit a person completes is now a course, not a lesson — the structural
change the 2026 CPE compliance work depends on. Both databases were
confirmed empty right before this shipped (0 rows in `attempts` and
`lessons`), so migration `05e053f86e0a` adds `courses`, moves `lessons`
under it (`course_id` FK not null, `position` unique per course, `slug`
still globally unique), and swaps `attempts.lesson_id` for
`attempts.course_id`, all with no backfill logic — the migration's own
docstring says why. `retake_cooldown_minutes`/`max_attempts` moved from
lessons to courses (a person retakes a course); `watch_progress`,
`questions`, and `choices` stay exactly where they were, deliberately.
`PASS_THRESHOLD = 4` is gone, replaced by `PASS_RATIO = 0.8` applied to a
course's total published-lesson question count and rounded up
(`math.ceil`) — identical behaviour on a five-question course (4/5) and
the generalised case proven with a fifteen-question course (12/15 passes,
11/15 doesn't). Backend: a new `app/services/courses.py`
(`list_published`, `get_by_slug`, `get_with_lessons`, plus
`published_question_count`, `get_published_lesson`, and
`get_lesson_in_course` for the segment page's prev/next links) backs a new
`app/routers/courses.py` that replaces `lessons.py`/`quiz.py`/`watch.py`
outright: `GET /courses`, `GET /courses/{slug}`, `GET
/courses/{slug}/lessons/{lesson_slug}` (+ its `video-url`/`thumbnail-url`/
`watch`), `GET /courses/{slug}/watch-status` (new — per-lesson progress
plus one `gate_met` bool from `watch.course_watch_status`, which just
reuses `get_progress`'s existing "no duration means unlocked" rule rather
than re-deriving it), `GET /courses/{slug}/quiz`, and `POST
/courses/{slug}/attempts`. `quiz.get_quiz_for_course` walks every
published lesson's published questions in lesson-then-question order for
free, since both relationships are already position-ordered — no extra
sort, and the leak test moved over unchanged. `attempts.start_attempt`
keeps feature 016's authenticate-then-gate-then-policy order, now against
a course, and a locked assessment names the specific outstanding segment
(`WatchRequirementNotMetError` carries its slug/title) rather than a bare
second count. `admin_content.py` gained full course CRUD, `create_lesson`/
`move_lesson`/`delete_lesson` nested under a course (reusing the existing
two-phase `_renumber` unchanged), and `validate_for_publish` now walks a
course: title/slug/description, at least one lesson, every lesson has a
video and at least one question, and the feature 010 per-question rules —
still one flat list of every failure at once. Publishing a course also
flips every one of its lessons to `is_published = True` in the same
transaction (there's no separate per-lesson publish action any more —
`validate_for_publish` already proved each one was complete); this was
caught by a test that actually re-fetched the public quiz after
publishing rather than only asserting `course.is_published`. Deleting a
course with completed attempts still 409s exactly as a lesson used to;
deleting a lesson now checks its *course's* attempts, so a segment can't
be pulled out from under an already-graded assessment either.
`app/services/analytics.py` re-keys its four aggregates on `course_id`,
and `question_stats`/`dropoff` now carry `lesson_title` per row (dropoff
groups by `question_id`, not raw position, since position resets inside
each lesson) so the admin can see which segment a bad question or a
drop-off point belongs to. Frontend: `CourseList`/`CourseDetail` replace
`LessonList`/`LessonDetail` (`CourseCard` reuses `LessonCard`'s 16:9 shape
plus a segment count), a new `LessonSegment` page plays one segment with
previous/next links, and `Quiz`/`Result`/`Progress`/`Verify` all take a
course slug and `course_title` now. `AdminCourseList` and a new
`AdminCourseEditor` (details, a generalised `ThumbnailUploader` moved to
`components/` so both course and lesson can reuse it, an ordered
`LessonsPanel` with add/move, and `CoursePublishPanel`) wrap the existing
`AdminLessonEditor`, which lost its own publish panel and now links back
to its course. The old `/lessons/:slug` routes are gone outright, no
redirect layer — there was no live traffic to preserve. Verified against
a real dev database end to end in a browser (Playwright): author a
three-lesson course, reorder it, publish it, watch all three segments as
a signed-in user, confirm the assessment button stays locked until every
segment is watched and names which one is outstanding, pass a
fifteen-question run at 12/15, and download the resulting certificate.
Learning objectives/program level/field of study (020), the development
and review chain (021), credit calculation (022), and splitting review
from assessment questions with a per-course pass threshold column (023)
remain out of scope.

## 2026-08-12, Feature 020, Program metadata and learning objectives
New `learning_objectives` table (`course_id` FK ondelete CASCADE, unique
`(course_id, position)`, `text`) plus four columns on `courses`:
`program_level`, `field_of_study` (both plain `String` with a hand-added
`CHECK` constraint and a Python constant, not a native Postgres enum —
NASBA revises these lists on its own schedule, and altering a native
enum in a migration is far more friction than editing a constant),
`prerequisites`, and `advance_preparation` (both nullable `Text`).
`app/constants/program_levels.py` and `app/constants/fields_of_study.py`
hold the allowed values, transcribed from
`docs/2026-Statement-on-Standards-for-CPE-Programs.pdf` and
`docs/2024-Fields-of-Study-Document.pdf` (both added to `docs/` this
feature) rather than from memory; fields of study carry a
technical/non-technical split alongside each value for a future
per-state non-technical credit cap, plus a `non_cpe` ("Not CPE
eligible") sentinel that's abacadaba's actual default, since its
content is deliberately non-financial. `admin_content.py` gained
`create_objective`/`update_objective`/`delete_objective`/
`move_objective`, reusing the existing two-phase `_renumber` unchanged
rather than a second implementation. `validate_for_publish` gained five
rules: at least one non-blank objective, a valid `program_level`, a
non-blank `field_of_study`, and — the one with real logic — Intermediate/
Advanced/Update courses must have both `prerequisites` and
`advance_preparation` non-empty (3.02.1's conditional-on-another-field
requirement), while Basic/Overview may leave both blank. `GET
/courses/{slug}` now returns all five pieces of metadata in the public
payload — the actual disclosure requirement, not just an admin-side
add. Two new unauthenticated endpoints, `GET /meta/fields-of-study` and
`GET /meta/program-levels`, feed the admin selects from the server
instead of duplicating NASBA's lists in JavaScript. Frontend:
`AdminCourseEditor` gained an `ObjectivesPanel`/`ObjectiveRow` pair that
reuse `QuestionsEditor`/`QuestionEditor`'s CSS modules directly rather
than forking them, and `CourseDetailsForm` gained a program-level
select, a field-of-study select with Technical/Non-technical `optgroup`s
("Not CPE eligible" first, selected by default for new courses),
and two textareas. `CourseDetail` renders a "What you will learn" list
and a program-details block — rendering literal "None" for blank
prerequisites/advance preparation rather than omitting the row, since
3.02.1 asks for a stated none — above both the lesson list and the
assessment button, so it's pre-enrollment disclosure rather than
something found after starting. `CoursePublishPanel` needed no changes:
the new failures surface automatically through its existing
`publishErrors` list, confirming feature 017's checklist design has no
gap here. Verified against a real dev database end to end in a browser
(Playwright): added, reordered, edited, and deleted objectives on a
live course; set an Intermediate course's level with blank prerequisites
and watched Publish block with the exact two missing-field messages;
filled them in, set field of study via the grouped select, and
published; confirmed the signed-out public page shows objectives,
level, field of study, prerequisites, and advance preparation above the
assessment button; and confirmed a Basic course with both fields left
blank publishes and renders "None" for both on its public page. Objectives
on individual lessons, and the development/review chain's "most recent
publication, revision, or review date" (021), remain out of scope.

## 2026-08-14, Feature 020a, Dirty-tracking defects in the questions and objectives editors
`DetailsForm` already reported its dirty state up to the page-level
`hasUnsavedWork` (the `beforeunload` warning and the "Back" link's
confirm dialog); the row editors for questions, choices, and learning
objectives did not, even though each row already computed its own
dirty flag locally to enable its own Save button. Editing a question
prompt, a choice, or an objective and then navigating away without
clicking that row's Save lost the edit silently. Extended the same
`onDirtyChange` pattern one level deeper: `ChoiceRow` and `ObjectiveRow`
now report `(id, dirty)` up; `QuestionEditor` combines its own prompt
dirty state with the OR of its choices' into one signal per question;
`QuestionsEditor` and `ObjectivesPanel` aggregate their rows' signals
(dirty-id `Set`s) into a single boolean each and report it up via their
own `onDirtyChange`; `AdminLessonEditor`'s and `AdminCourseEditor`'s
`hasUnsavedWork` now OR in `questionsDirty`/`objectivesDirty` alongside
the existing `detailsDirty`/`uploading`. The three aggregator callbacks
(`QuestionsEditor`, `QuestionEditor`, `ObjectivesPanel`) needed
`useCallback` — without a stable identity, each child row's dirty-effect
depends on the callback reference, and a fresh function every render
put React into an infinite `setState`-in-`useEffect` loop
("Maximum update depth exceeded"), caught during manual browser
verification (Playwright) before shipping, not by lint or pytest. No
Save button moved, no save granularity changed — that's 020b, next.
Verified against a live dev database via a scripted Playwright session:
editing an objective, a question prompt, and a choice each independently
triggers the confirm dialog on navigating away when unsaved and does not
when clean or after that row's own Save is clicked; console stayed free
of repeated render-loop errors through all three. `npm run lint` and the
full backend `pytest` suite (183 tests, unchanged) both pass.

## 2026-08-14, Feature 020b, Authoring workflow
One save model, field labels, a restructured questions editor, an explicit
next step, and orientation text for an empty course — five presentation-only
fixes from watching one person author a course start to finish. All Details,
Objectives, Questions, and Choices edits are now held in client state and
committed by a single sticky `StickySaveBar` (new, `components/StickySaveBar`)
pinned to the bottom of each editor page, showing a live count of unsaved
changes and inert at zero; every per-row Save button (`ChoiceRow`,
`QuestionEditor`'s prompt, `ObjectiveRow`, `DetailsForm`, `CourseDetailsForm`)
is gone. Reaching this from 020a's per-row dirty booleans meant widening the
contract to counts and adding a matching commit path: each row now exposes a
`save()` via `useImperativeHandle` (fresh closure every render, since a
memoized handle would go stale the way the naive dirty-callback did in 020a),
and each aggregator (`QuestionEditor` over its choices, `QuestionsEditor` over
its questions, `ObjectivesPanel` over its objectives) holds a `Map` of child
refs alongside its `Map` of dirty counts and sums both on the way up; the
page's `handleSaveAll` calls whichever refs are actually dirty, awaits them
together, and only then refetches. Delete/Move/Add/upload stayed immediate —
uploads now say so explicitly in both `VideoUploader` and the shared
`ThumbnailUploader` ("saves immediately... unlike the rest of this page").
`ThumbnailUploader` gained `label`/`placementNote` props so the course and
lesson thumbnail sections read as what they are ("Course thumbnail — shown on
the course card in the catalog" vs "Lesson thumbnail — the poster frame shown
before this segment's video plays"); `CourseDetailsForm`'s description field
is now labelled "Course description" with a hint naming it the 8.01.1
pre-enrollment disclosure, and `DetailsForm`'s lesson description got its own
hint. In `QuestionEditor`, choices moved into a `.choicesBlock` — indented,
left-ruled, surface-tinted — so they read as belonging to their question
instead of just trailing it, and `QuestionsEditor` moved "Add question" (now
a textarea, matching a prompt's shape rather than a choice's single-line
input) into a dashed full-width block above the question list instead of
below the last one, so it can no longer sit directly under an "Add choice"
input. Objectives have no nested add-control, so no equivalent adjacency
existed there and `ObjectivesPanel` is unchanged in that respect.
`AdminLessonEditor` gained a "Next" section — reusing `checkAdminCoursePublish`
(previously course-editor-only) filtered to messages starting with `Lesson
'<this lesson's title>'`, stripped of that prefix — showing what's still
outstanding or confirming the lesson is publish-ready, plus a repeated "Back
to course" link, both above the danger zone. `CoursePublishPanel`'s per-lesson
failure messages now match that same `Lesson '<title>'` pattern against
`course.lessons` and render as links to `/admin/lessons/{id}` when a match is
found; its publish-blocked reasoning generalized from a details-only
`detailsDirty` prop to `hasUnsavedWork`, since unsaved objective edits are
just as stale-publish-worthy as unsaved details now. `LessonsPanel` shows
orientation text — what a lesson is, and that a course is one or more of them
in order — only while `course.lessons.length === 0`, replaced by the list
once one exists. Verified against a live dev database via a scripted
Playwright session covering both editors end to end: created a course,
confirmed the empty-lessons orientation text, edited a detail field and an
objective and saved both with one click, confirmed the unsaved-changes dialog
fires on a dirty question prompt and a dirty choice and clears after save,
confirmed a hard-reloaded page shows the persisted values (not just local
state), watched the lesson's "Next" section drop "must have at least one
question" once a question with two choices and a correct answer existed,
and clicked a lesson-named publish-checklist failure through to that lesson's
editor. `npm run lint` and the full backend `pytest` suite (183 tests,
unchanged — no backend file touched) both pass. This feature is entirely
presentation and client state in the admin tool; `ThumbnailUploader`, the one
shared component touched, is never used on the public course page, so no
participant-facing disclosure changed. COMPLIANCE.md gains no row: the
8.01.1 and 3.02.1 mappings from feature 020 are unchanged and still accurate
against `docs/2026-Statement-on-Standards-for-CPE-Programs.pdf`, and Part 2's
relabelling did not surface any field mapped in 020 that turned out to be
unrendered. 020a's three dirty-tracking defects, background/resumable
upload, bulk question import, and certificate design remain out of scope, as
specified.

## 2026-08-18, Feature 020c, Authoring hotfix
Three of the four defects reported after 020a/020b were real; the fourth —
"the course description does not persist" — was not reproducible against the
shipped code and nothing changed for it beyond a regression test. Before
touching anything, the described mechanism (batched save assembling its
payload from a dirty-tracking path that skips the description textarea) was
checked directly: `CourseDetailsForm`'s `dirty` computation and its `save()`
already include `description` unconditionally, and a live round trip — API
calls straight against `TestClient` and a full scripted Playwright session
against the real dev server (fresh course creation, a second edit on an
existing course, human-paced typing, SPA back-navigation instead of a hard
reload, an objective added mid-edit, a hard reload) — persisted the field
correctly every time, for every field on both the course and lesson details
forms. `tests/test_admin_content.py` gained
`test_update_course_round_trips_every_field_on_the_details_form_in_one_batch`
as the regression guard the feature asked for regardless. COMPLIANCE.md's
8.01.1 row needs no Gap update: the pre-enrollment disclosure it points at
works, and nothing suggests it stopped working between 020b and this feature.

Bug 2, quiz numbering, was real and was never fixed despite 020a's changelog
entry implying otherwise — 020a's actual entry (see above) covers only the
dirty-tracking defects, not this. The mechanism was exactly as suspected but
in a different layer than the hypothesis in this file guessed: `GET
/courses/{slug}/quiz` (`app/routers/courses.py`) built each `QuestionPublic`
with `position=question.position`, the question's authored/DB position,
even though the *list* it was iterating had already been reordered by
`shuffle_questions` — so `QuestionCard.jsx`, which has always rendered
`question.position` faithfully, was correctly displaying an incorrect number.
Fixed by numbering from the served order instead:
`enumerate(questions, start=1)` supplies `position` now, so it's 1..N in
whatever order (shuffled or not) the questions actually went out in — no
frontend change needed. `tests/test_shuffle.py` gained
`test_shuffled_question_position_matches_served_order_not_authored_order`,
using seed 7 (confirmed to reorder these five questions) as a regression
guard that fails against the pre-fix code. Verified in a browser as a signed
in non-admin: took a five-question quiz end to end, and the card's leading
number matched the progress bar's "Question N of 5" on every question.

Bug 3, the add-question control: kept it above the list (020b's fix for the
"Lava" mis-entry adjacency stands, unmoved). `QuestionEditor` now exposes
`focusPrompt()` via its imperative handle — scrolls its prompt textarea into
view and focuses it — and `QuestionsEditor` remembers the id `createAdminQuestion`
just returned, then calls that method once the refreshed `lesson.questions`
prop actually contains it. No workaround was needed for the page's scroll
container; plain `scrollIntoView` was sufficient. Verified in a browser:
adding a fifth question to a lesson that already had four scrolled the page
and left the new question's prompt textarea focused.

Bug 4, the vacuous publish check: `CoursePublishPanel` rendered its one
per-lesson rule ("every lesson has a video, at least one question...") as a
green check whenever `course.lessons` produced no per-lesson error messages —
true both when every lesson actually passed and when there were no lessons to
fail. Now branches on `course.lessons.length === 0` first and renders that
line `○` (neutral) in that case, `✓` only when there's at least one lesson and
none of them produced an error. Verified in a browser against a freshly
created, lesson-less course: the checklist showed `○` for both "at least one
lesson" and the per-lesson rule, no green check on either.

Backend: `app/routers/courses.py` (quiz numbering).
Frontend: `QuestionEditor.jsx`, `QuestionsEditor.jsx` (scroll/focus),
`CoursePublishPanel.jsx` (neutral checklist state). Tests:
`tests/test_admin_content.py`, `tests/test_shuffle.py`. `npm run lint` and
the full backend `pytest` suite (185 tests: 183 unchanged + 2 new) both pass.
COMPLIANCE.md gains no row and no Gap update: bug 1 turned out not to be a
defect, and bugs 2 through 4 are assessment-taking and admin-tool display/UX
correctness with no Standards locator to map to — confirmed against
`docs/2026-Statement-on-Standards-for-CPE-Programs.pdf`, not assumed.
Background/resumable upload, collapsing single-lesson courses, bulk question
import, certificate design, and any schema change remain out of scope, as
specified.

## 2026-08-18, Feature 020d, The save affordance
A shared `Button` component (`primary`/`secondary`/`danger`, plus a `disabled`
modifier that wins over every variant via the native `disabled` attribute) now
backs every button in the admin — no shared button module existed yet despite
the feature assuming one, so this feature created it rather than editing one.
The bottom save bar (`StickySaveBar`) is hidden when the page is clean and
slides in under 200ms when it becomes dirty, with `aria-live="polite"`; a
second Save button now sits in the page header next to the title, sharing the
same dirty/saving state and handler as the bar so there is one source of
truth. Course and lesson detail forms, and each objective/question/choice
row, mark the individual field that changed with a left border accent, using
the already-loaded server snapshot each form compares against (no new client
state was needed — 020b's batched state already held per-field original
values, not just a boolean). Cmd/Ctrl+S saves when dirty and is bound only on
the two editor pages. Leaving an editor with unsaved changes now blocks
in-app navigation via react-router's `useBlocker` (which required migrating
`main.jsx` from `BrowserRouter` to `createBrowserRouter`/`RouterProvider`,
since `useBlocker` only works under a data router) and `beforeunload` for tab
close/reload, as before. Video and thumbnail uploads remain outside the
batched save and do not dirty the bar. Verified in a live browser session
(Playwright driving a dev server): disabled Save renders grey/`not-allowed`
next to a light-purple enabled `Add lesson`, editing a field turns the header
Save solid purple and marks the field, dismissing the nav-guard confirm
keeps you on the page, Cmd+S saves and clears every marker, and the Publish
checklist reflects the save on a fresh fetch. Backend untouched;
`pytest` (185 tests) passes unchanged.
COMPLIANCE.md gains no row: this is an authoring-tool rendering and
interaction fix with no Standards locator to map to. Content silently
failing to save would touch Section 9's documentation requirements, but
that was never the defect here — the data was always saved correctly on
click, the author just couldn't tell.
